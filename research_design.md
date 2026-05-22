案命名为 **ELP-Atlas: Learning-Progress Guided Self-Evolution with Capability Atlas**。

核心论文主张是：

> 现有 self-evolution 多数用“难度”“不确定性”“多样性”近似训练价值；但真正重要的是：**这个样本是否能让 Solver 在能力边界上产生可测的学习进步，同时不导致旧能力遗忘。**
> 我们提出 Expected Learning Progress reward + Capability Atlas，让 Challenger/Generator 学会生成“真正能让自己进步”的数据。

这个方案主要对标 R-Zero / R-Diverse / Tool-R0 / SAGE / G-Zero / TPAW。R-Diverse 已经指出 self-play 里会出现 **Diversity Illusion**，并用 MAP 和 SAM 分别处理跨轮重复与 skill-level diversity；Tool-R0 证明了 Generator-Solver zero-data tool-use self-play 的可行性；SAGE 引入 Challenger、Planner、Solver、Critic 四角色并依赖 verifier；G-Zero 用 Hint-δ 做 verifier-free open-ended self-play；TPAW 则把历史 checkpoint 作为 team 成员来稳定 self-play。([arXiv][1])

---

# 0. 最终论文要讲的故事

论文标题可以叫：

**ELP-Atlas: Self-Evolving LLMs by Generating What They Can Actually Learn**

主 claims：

1. **Learning-progress reward 比 difficulty / uncertainty reward 更接近 self-evolution 的本质。**
   难题不一定有训练价值；重复题、噪声题、超出能力边界太远的题都会浪费训练。

2. **Capability Atlas 比 memory bank 更强。**
   R-Diverse 的 MAP/SAM 已经证明 sample-level diversity 不够；我们进一步维护 skill graph，主动决定下一轮该训练哪些能力节点。

3. **Anti-regression 是长期自进化的必要组件。**
   自进化不能只看新能力提升，还要防止旧能力被新生成数据冲坏。

4. **ELP-Atlas 在长轮数 self-play 中更稳定。**
   baseline 通常 3–5 轮后收益变小或 collapse；我们的目标是 10–20 轮仍有持续或至少非退化提升。

---

# 1. 实验总体设置

建议做两个主实验域，一个辅助开放域实验。

## Domain A：数学 / 通用推理，主线实验

这是最适合发主论文的实验域，因为 verifier 明确，R-Diverse / SAGE 都可对标。

**训练数据来源：**

* zero-data 版本：不使用人工训练题，只给任务类型说明和 verifier。
* small-seed 版本：给 300–500 个 seed examples，对标 SAGE。SAGE 本身是 small seed + automatic verifier 的多 agent framework，包含 Challenger、Planner、Solver、Critic 四角色。([arXiv][2])

**生成任务类型：**

* arithmetic word problem
* algebra
* counting / combinatorics
* symbolic manipulation
* table reasoning
* multi-hop logical reasoning
* code-style algorithmic reasoning，可选

**评测集：**

* GSM8K test
* MATH500
* SVAMP
* ASDiv
* BBH subset
* OlympiadBench subset
* Minerva Math subset
* ARC-Challenge，可选
* DROP subset，可选

其中 GSM8K / MATH500 / SVAMP / ASDiv 用来测试基本数学泛化，BBH / ARC / DROP 测试是否只过拟合到数学模板。

---

## Domain B：tool-use / function calling，强辅助实验

这个域非常适合证明方法不是只对数学有效。Tool-R0 已经建立了 zero-data Generator-Solver tool-learning 框架：Generator 生成挑战性工具调用任务，Solver 学习真实工具调用，并且论文报告了 92.5% relative improvement。([arXiv][3])

**训练数据来源：**

* synthetic tool schemas
* mock executable tools
* generated user requests
* generated gold tool calls
* deterministic verifier

**工具类型：**

* calculator
* calendar
* database lookup
* weather mock API
* travel booking mock API
* shopping/inventory mock API
* email / messaging mock API
* multi-tool dependency API

**评测集：**

* BFCL fixed snapshot
* ToolBench subset
* APIBench subset
  -自建 held-out synthetic tool set，工具 schema 完全不与训练重合

**核心指标：**

* tool selection accuracy
* argument accuracy
* full call exact match
* multi-call dependency correctness
* invalid JSON / invalid schema rate
* execution success rate

---

## Domain C：open-ended generation，可作为扩展实验

这个不建议作为第一主线，因为评价难。但可以作为一个漂亮 extension：把 ELP-Atlas 接到 G-Zero 风格的 verifier-free setting。G-Zero 的核心是 Hint-δ，即比较无 hint 和有 hint 时 Generator 响应分布的 shift，并用 GRPO 训练 Proposer、DPO 训练 Generator。([arXiv][4])

这里不要一上来做大，建议只做：

* instruction following
* structured writing
* summarization with constraints
* critique/revision

开放域实验只回答一个问题：

> ELP-style sample selection 能不能降低 G-Zero 类方法的 collapse / hint artifact / answer leakage？

---

# 2. 模型与训练基础配置

## 2.1 Base models

建议至少做三个规模：

| Scale  | Model                                | 用途                 |
| ------ | ------------------------------------ | ------------------ |
| small  | Qwen2.5-1.5B-Instruct 或 Qwen2.5-1.5B | 快速调参、长轮数 20 rounds |
| medium | Qwen2.5-3B-Instruct                  | 主实验                |
| large  | Qwen2.5-7B-Instruct 或 Qwen2.5-7B     | 最终强结果              |

如果资源允许，可以加 Qwen3-4B / Qwen3-8B，因为 R-Diverse 报告里也使用了 Qwen3 规模模型来验证持续多轮 self-play 的效果。([arXiv][1])

## 2.2 角色模型

每个角色用同一个 base model 初始化，但用独立 LoRA adapter。

核心角色：

1. **Challenger / Generator**
   生成训练任务、答案、verifier、skill metadata。

2. **Solver**
   学习解题或工具调用。

3. **Skill Abstractor**
   把任务映射到 skill node。可以是 frozen LLM prompt，也可以是规则 + embedding。

4. **Critic / Filter**
   只做质量过滤，不做最终 reward judge。避免退化成 LLM-as-a-judge。

5. **Probe Adapter**
   临时 LoRA，用来估计 learning progress，不进入最终模型。

可选角色：

6. **Planner**
   对标 SAGE，用于生成 structured solution plan。

7. **Historical Solvers**
   对标 TPAW，把过去 checkpoints 作为 team members，用于估计遗忘、分歧和训练价值。TPAW 的核心就是让当前 policy 与历史 checkpoint 协作和竞争，并使用 adaptive weighting 稳定 self-play。([arXiv][5])

---

# 3. ELP-Atlas 核心算法

## 3.1 记号

每个生成样本记为：

[
\tau = (x, y^*, v, z)
]

其中：

* (x)：生成的问题 / 用户请求；
* (y^*)：生成的参考答案、工具调用或程序；
* (v)：verifier；
* (z)：skill representation；
* (S_\theta)：当前 Solver；
* (G_\phi)：当前 Challenger；
* (A)：Capability Atlas。

每个 skill node (i) 维护：

[
A_i = (c_i, u_i, lp_i, f_i, n_i, e_i)
]

含义：

* (c_i)：当前 Solver 在该 skill 上的 competence；
* (u_i)：uncertainty；
* (lp_i)：最近 learning progress；
* (f_i)：forgetting risk；
* (n_i)：该 skill 历史样本密度；
* (e_i)：到其他 skill 的 transfer edges。

---

## 3.2 Capability Atlas 构建

### Step 1：生成 skill representation

对每个样本生成一个结构化 skill record：

```json
{
  "domain": "math",
  "skill_tags": [
    "multi_step_arithmetic",
    "linear_equation",
    "entity_tracking"
  ],
  "reasoning_ops": [
    "extract_quantities",
    "build_equation",
    "solve_equation",
    "check_units"
  ],
  "failure_modes_targeted": [
    "entity_confusion",
    "missing_constraint"
  ],
  "difficulty_estimate": 0.62,
  "dependency_tags": [
    "arithmetic",
    "symbolic_manipulation"
  ]
}
```

对于 tool-use：

```json
{
  "domain": "tool_use",
  "skill_tags": [
    "tool_selection",
    "argument_grounding",
    "multi_call_dependency"
  ],
  "tool_graph": [
    ["search_inventory", "reserve_item"],
    ["reserve_item", "send_confirmation"]
  ],
  "argument_types": [
    "date",
    "location",
    "product_id"
  ],
  "failure_modes_targeted": [
    "wrong_tool",
    "extra_argument",
    "missing_dependency"
  ]
}
```

### Step 2：转 embedding

推荐两种实现：

**低依赖版本：**

* 把 skill record 序列化成字符串；
* 用当前 base model 的最后一层 hidden states mean pooling 得到 embedding；
* 不引入额外 encoder。

**强性能版本：**

* 使用 frozen sentence embedding model；
* 注意所有方法都用同一个 encoder，保证公平。

### Step 3：online clustering

伪代码：

```python
def assign_skill_node(skill_emb, atlas, threshold=0.78):
    if atlas.is_empty():
        return atlas.create_node(skill_emb)

    nearest_node, sim = atlas.nearest(skill_emb)

    if sim < threshold:
        return atlas.create_node(skill_emb)
    else:
        atlas.update_centroid(nearest_node, skill_emb)
        return nearest_node
```

每轮更新：

```python
node.competence = ema(node.competence, solver_pass_rate)
node.uncertainty = sqrt(node.competence * (1 - node.competence) / (node.count + 1))
node.learning_progress = ema(node.learning_progress, observed_delta)
node.forgetting_risk = max(0, old_competence - new_competence)
node.density = log(1 + node.count)
```

---

# 4. Expected Learning Progress reward

这是整篇论文最关键的部分。

## 4.1 为什么不用单纯 difficulty reward

现有 self-play 常用：

[
R_{\text{difficulty}} = \mathbb{1}[p_{\min} < p_{\text{solver}} < p_{\max}]
]

或者：

[
R_{\text{uncertainty}} = p(1-p)
]

问题是：

* 难不代表可学；
* 高不确定可能只是噪声；
* frontier 任务可能重复；
* task 太偏会导致训练后遗忘；
* Generator 可能 reward hack，生成奇怪格式或不可学习题。

所以我们直接估计：

[
R_{\text{ELP}}(\tau) =
\Delta \text{Perf}_{\text{frontier}}
------------------------------------

## \lambda_{\text{reg}} \Delta \text{Regress}_{\text{old}}

## \lambda_{\text{noise}} \text{Noise}

\lambda_{\text{cost}} \text{Cost}
+
\lambda_{\text{novel}} \text{Novelty}
]

---

## 4.2 Learning progress 的三种估计

### 估计方式 A：gradient alignment，便宜，适合大规模筛选

对候选样本 (\tau) 计算 supervised loss 或 RL surrogate loss：

[
g_\tau = \nabla_\theta L(\tau; \theta)
]

对 frontier memory 里的样本 (m) 计算：

[
g_m = \nabla_\theta L(m; \theta)
]

一次小更新后，memory loss 的一阶近似下降为：

[
\Delta L_m \approx \eta g_m^\top g_\tau
]

所以定义：

[
\widehat{LP}_{\text{grad}}(\tau)
================================

\frac{1}{|M_f|}
\sum_{m \in M_f}
\text{clip}
\left(
\frac{g_m^\top g_\tau}{|g_m||g_\tau|},
-1,
1
\right)
]

只在 LoRA 参数上算梯度，不在全模型上算。

### 估计方式 B：micro-probe update，中等成本，适合 rerank

对 top 候选做一个临时 LoRA update：

[
\theta' = \theta - \alpha \nabla_\theta L(\tau; \theta)
]

然后在 frontier memory 和 old memory 上评估：

[
LP_{\text{probe}}(\tau)
=======================

## \text{Score}(S_{\theta'}, M_f)

\text{Score}(S_\theta, M_f)
]

[
Reg_{\text{probe}}(\tau)
========================

\max
\left(
0,
\text{Score}(S_\theta, M_o)
---------------------------

\text{Score}(S_{\theta'}, M_o)
\right)
]

### 估计方式 C：behavioral delta，最稳但最贵

对一个 candidate batch 做 probe training，然后观察：

* pass@1 是否提升；
* verifier score 是否提升；
* tool-call exact match 是否提升；
* format error 是否下降；
* old skills 是否退化。

这个适合每轮最终选样前做一次 group-level reranking。

---

## 4.3 推荐实际实现：两阶段 ELP

为了避免太贵，实际执行用两阶段：

### Stage 1：cheap ELP prefilter

对每轮生成的 (B=4000) 个候选：

1. 过滤 invalid / noisy；
2. 计算 Solver pre-success；
3. 计算 skill novelty；
4. 计算 gradient alignment；
5. 每个 skill node 保留 top-k。

### Stage 2：probe rerank

对 Stage 1 保留下来的 (B'=800) 个候选：

1. 按 skill node 分组；
2. 每组随机取 8–16 个样本；
3. 做 1–3 step LoRA probe update；
4. 在 frontier memory + old memory 上评估；
5. 得到最终 ELP score；
6. 选 top (N=1000) 或 (N=2000) 个样本训练 Solver。

---

## 4.4 Challenger reward 公式

最终给 Challenger 的 reward：

[
R_G(\tau)
=========

w_1 \cdot \text{norm}(LP_{\text{probe}})
+
w_2 \cdot \text{frontier}(c_i)
+
w_3 \cdot \text{novelty}(z)
---------------------------

## w_4 \cdot Reg_{\text{probe}}

## w_5 \cdot Noise(\tau)

w_6 \cdot Cost(\tau)
]

其中：

[
\text{frontier}(c_i) = 4c_i(1-c_i)
]

这个函数在 (c_i=0.5) 时最大，表示 skill 位于能力边界。

[
\text{novelty}(z) =
1 -
\max_{m \in M}
\cos(z, z_m)
]

[
Noise(\tau)
===========

1 -
\text{confidence}(\tau)
]

confidence 可以由以下组成：

```python
confidence = (
    verifier_pass
    * format_validity
    * answer_consistency
    * non_leakage_score
    * solvability_score
)
```

推荐初始权重：

```yaml
w_lp: 1.00
w_frontier: 0.30
w_novelty: 0.25
w_regression: 0.70
w_noise: 0.80
w_cost: 0.05
```

---

# 5. Capability Atlas acquisition function

每轮 Challenger 不是随机出题，而是先从 Atlas 里选择 skill target。

对每个 skill node (i)，计算：

[
Q_i
===

\alpha lp_i
+
\beta u_i
+
\gamma 4c_i(1-c_i)
------------------

\delta \log(1+n_i)
+
\rho f_i
+
\eta T_i
]

其中：

* (lp_i)：最近 learning progress；
* (u_i)：不确定性；
* (4c_i(1-c_i))：frontier score；
* (\log(1+n_i))：密度惩罚；
* (f_i)：遗忘风险，遗忘高的节点需要 replay；
* (T_i)：transfer potential。

默认参数：

```yaml
alpha_learning_progress: 1.0
beta_uncertainty: 0.4
gamma_frontier: 0.5
delta_density: 0.3
rho_forgetting: 0.6
eta_transfer: 0.2
sampling_temperature: 0.8
```

采样：

[
P(i) = \text{softmax}(Q_i / T)
]

每轮生成任务时：

```python
target_nodes = sample_skill_nodes(atlas, num_targets=256)
for node in target_nodes:
    challenger.generate_tasks(skill_node=node, n=16)
```

---

# 6. 完整训练循环

下面是可以直接交给 agent 实现的 loop。

```python
for round_id in range(num_rounds):

    # 1. Sample skill targets from Capability Atlas
    target_nodes = atlas.sample_nodes(
        acquisition="learning_progress_frontier_novelty",
        num_nodes=config.num_target_nodes
    )

    # 2. Challenger generates candidate tasks
    candidates = []
    for node in target_nodes:
        candidates += challenger.generate(
            skill_node=node,
            num_samples=config.samples_per_node,
            schema=config.task_schema
        )

    # 3. Basic validation
    candidates = filter_format(candidates)
    candidates = filter_verifier_validity(candidates)
    candidates = filter_answer_leakage(candidates)
    candidates = filter_length_and_cost(candidates)

    # 4. Estimate current Solver competence on candidates
    for tau in candidates:
        tau.pre_score = evaluate_solver_pre_success(
            solver=current_solver,
            task=tau,
            num_rollouts=config.pre_eval_rollouts,
            verifier=tau.verifier
        )

    # 5. Skill abstraction and Atlas assignment
    for tau in candidates:
        tau.skill_record = skill_abstractor(tau)
        tau.skill_emb = encode_skill(tau.skill_record)
        tau.skill_node = atlas.assign(tau.skill_emb)

    # 6. Cheap ELP scoring
    for tau in candidates:
        tau.grad_lp = estimate_gradient_learning_progress(
            solver=current_solver,
            candidate=tau,
            frontier_memory=atlas.frontier_memory(tau.skill_node),
            lora_params_only=True
        )

        tau.novelty = atlas.skill_novelty(tau.skill_emb)
        tau.noise = estimate_noise(tau)
        tau.frontier = 4 * tau.pre_score * (1 - tau.pre_score)

        tau.cheap_score = (
            w_lp_cheap * tau.grad_lp
            + w_frontier * tau.frontier
            + w_novelty * tau.novelty
            - w_noise * tau.noise
        )

    # 7. Keep top candidates per skill node
    shortlisted = select_top_per_skill(
        candidates,
        score_key="cheap_score",
        top_k=config.top_k_per_skill
    )

    # 8. Probe update reranking
    probe_groups = group_by_skill(shortlisted, group_size=config.probe_group_size)

    for group in probe_groups:
        theta_probe = clone_lora(current_solver)
        theta_probe.train_on(group, steps=config.probe_steps)

        lp = evaluate_delta(
            before=current_solver,
            after=theta_probe,
            eval_set=atlas.frontier_memory(group.skill_node)
        )

        reg = evaluate_regression(
            before=current_solver,
            after=theta_probe,
            eval_set=atlas.old_memory()
        )

        for tau in group:
            tau.probe_lp = lp
            tau.probe_reg = reg
            tau.final_reward = compute_generator_reward(tau)

    # 9. Train Challenger with GRPO / REINFORCE
    challenger.update(
        prompts=target_nodes,
        completions=candidates,
        rewards=[tau.final_reward for tau in candidates],
        method="GRPO",
        kl_to_base=config.challenger_kl
    )

    # 10. Select Solver training data
    train_batch = select_solver_training_data(
        shortlisted,
        score_key="final_reward",
        num_samples=config.solver_train_samples,
        balance_by_skill=True,
        include_replay=True,
        replay_memory=atlas.replay_memory()
    )

    # 11. Train Solver
    solver.update(
        train_batch,
        method=config.solver_method,  # GRPO/RLVR or DPO/SFT
        verifier_based_reward=True,
        kl_to_previous=config.solver_kl
    )

    # 12. Evaluate
    eval_results = evaluate_all_benchmarks(solver)

    # 13. Update Atlas
    atlas.update(
        train_batch=train_batch,
        eval_results=eval_results,
        candidate_stats=candidates,
        solver=current_solver
    )

    # 14. Save checkpoints
    save_round_checkpoint(round_id, solver, challenger, atlas, eval_results)
```

---

# 7. 训练细节

## 7.1 Challenger 训练

推荐使用 GRPO，因为 G-Zero、Tool-R0、SAGE 都采用或接近 group-relative / RL-style 的训练范式，便于公平比较。G-Zero 明确使用 GRPO 训练 Proposer，并用 DPO 训练 Generator；SAGE 则使用 per-role advantage normalization 的 self-evolution pipeline。([arXiv][4])

Challenger prompt 输入：

```text
You are generating a training task for a Solver.

Target skill node:
{skill_node_description}

Current Solver competence:
{competence}

Known failure modes:
{failure_modes}

Generate a task that:
1. Requires the target skill.
2. Is solvable and unambiguous.
3. Includes a verifiable final answer.
4. Avoids copying previous tasks.
5. Avoids leaking the answer in the problem.
6. Produces a JSON object following the schema.
```

输出 schema：

```json
{
  "problem": "...",
  "answer": "...",
  "solution_outline": "...",
  "verifier": {
    "type": "exact_match | symbolic | unit_test | tool_call",
    "spec": "..."
  },
  "skill_record": {
    "domain": "...",
    "skill_tags": [],
    "reasoning_ops": [],
    "failure_modes_targeted": []
  },
  "difficulty_rationale": "...",
  "anti_leakage_check": "..."
}
```

GRPO 设置：

```yaml
challenger:
  method: grpo
  rollouts_per_prompt: 8
  lr: 1.0e-5
  batch_size: 64
  max_prompt_len: 2048
  max_completion_len: 1024
  kl_coef: 0.02
  entropy_coef: 0.01
  reward_normalization: group
  lora_rank: 32
  lora_alpha: 64
```

---

## 7.2 Solver 训练

### 数学 / 推理域

推荐主方法：**GRPO / RLVR**。

每个 generated task 采样 (K=4) 或 (K=8) 个 Solver responses，用 verifier 评分：

```python
reward = (
    1.0 * answer_correct
    + 0.1 * format_correct
    + 0.1 * reasoning_complete
    - 0.2 * invalid_output
)
```

如果 verifier 只能判断 final answer，reasoning_complete 不进入主 reward，最多作为 filter。

Solver config：

```yaml
solver:
  method: grpo
  rollouts_per_task: 8
  lr: 5.0e-6
  batch_size: 128
  max_prompt_len: 2048
  max_completion_len: 2048
  kl_coef: 0.03
  entropy_coef: 0.00
  lora_rank: 64
  lora_alpha: 128
  train_epochs_per_round: 1
```

### tool-use 域

reward：

```python
reward = (
    0.4 * valid_json
    + 0.3 * valid_schema
    + 0.6 * correct_tool_selection
    + 0.8 * correct_arguments
    + 1.0 * execution_success
    + 0.5 * correct_multi_call_dependency
    - 0.3 * extra_call_penalty
)
```

最终也报告 binary full success。

---

## 7.3 Probe update 设置

Probe adapter 不保存，只用于估计样本训练价值。

```yaml
probe:
  lora_rank: 8
  lora_alpha: 16
  lr: 2.0e-5
  steps: 1
  batch_size: 8
  frontier_memory_size: 64
  old_memory_size: 128
  eval_rollouts: 1
```

为了省算力：

* small model：每个候选都算 gradient ELP，top 30% 做 probe；
* medium model：每组 skill 做 probe；
* large model：只用 gradient ELP + 小量 probe 校准。

---

# 8. Baselines

所有 baseline 必须共享：

* 同一个 base model；
* 同样生成 token budget；
* 同样训练 token budget；
* 同样 verifier；
* 同样 Solver update method；
* 同样评测集；
* 同样 rounds；
* 同样 random seeds。

否则审稿人会说不公平。

---

## Baseline 0：Base model

不训练，直接评测。

用途：确认 self-evolution 是否真的提升。

---

## Baseline 1：Seed SFT / Seed RLVR

只用 seed examples 训练，不做 self-play。

适用于 small-seed protocol。

---

## Baseline 2：Random Self-Training

Challenger 不训练，只随机生成任务，经相同 filter 后训练 Solver。

目的：证明提升不是“合成数据越多越好”。

---

## Baseline 3：Difficulty-only Self-Play

对标 R-Zero / Tool-R0 风格。

reward：

[
R = 4p(1-p)
]

其中 (p) 是当前 Solver 对该任务的 success rate。

Tool-R0 本身的核心就是让 Generator 生成 Solver competence frontier 附近的任务，因此这是必须 baseline。([arXiv][3])

---

## Baseline 4：Uncertainty-only Self-Play

reward：

[
R = \text{Var}(\text{Solver rollouts})
]

或：

[
R = p(1-p)
]

目的：比较 ELP 是否比不确定性更好。

---

## Baseline 5：Surface Diversity Self-Play

reward：

[
R = 1 - \max \cos(e_x, e_{x_{\text{history}}})
]

只看问题文本 embedding 多样性。

目的：证明 surface diversity 不够。

---

## Baseline 6：R-Diverse-style MAP + SAM

实现：

* MAP：跨迭代 memory penalty；
* SAM：用 skill-level representation 衡量多样性；
* 不使用 ELP reward。

R-Diverse 是最重要 baseline，因为它直接针对 Diversity Illusion：local diversity illusion 和 surface diversity illusion。([arXiv][1])

---

## Baseline 7：SAGE-style Multi-Agent

实现：

* Challenger 生成题；
* Planner 生成 plan；
* Solver 解题；
* Critic filter；
* verifier 判定正确性；
* 不使用 ELP；
* 不使用 Capability Atlas acquisition。

SAGE 是多 agent + small seed + verifier 的强 baseline，尤其在 math/code reasoning 上必须对比。([arXiv][2])

---

## Baseline 8：TPAW-style Historical Team

实现：

* 保留最近 (k=3) 个 Solver checkpoints；
* 当前 Solver 与历史 Solver 共同评估 candidate；
* 使用 adaptive weighting；
* 不使用 ELP probe；
* 不使用 Atlas acquisition。

目的：看 historical checkpoint team 是否能替代 learning-progress reward。TPAW 的动机是降低 synthetic data instability，并缓解迭代训练中正负样本差距变小的问题。([arXiv][5])

---

## Baseline 9：G-Zero-style Hint-δ，开放域扩展

只用于 Domain C。

实现：

* Proposer 生成 query + hint；
* Generator 无 hint 生成 response；
* Generator 有 hint 生成 response；
* 用 Hint-δ 评分；
* 用 DPO 内化 hint-guided response。

G-Zero 是 verifier-free open-ended self-play 的直接 baseline。([arXiv][4])

---

# 9. Main method variants

主方法建议至少做三个版本。

## Ours-ELP

只有 Expected Learning Progress reward，没有 Atlas acquisition。

目的：证明 ELP 本身有效。

---

## Ours-Atlas

有 Capability Atlas acquisition 和 novelty / anti-density，但没有 probe-based ELP。

目的：证明 Atlas 本身有效。

---

## Ours-ELP-Atlas

完整方法：

* Capability Atlas；
* ELP reward；
* anti-regression；
* skill-balanced replay；
* Challenger GRPO；
* Solver GRPO/RLVR。

这是主结果。

---

# 10. 实验矩阵

## 10.1 最小可行实验，MVP

目标：2 周内出第一批可信结果。

| 设置                             | 值                                                                   |
| ------------------------------ | ------------------------------------------------------------------- |
| Domain                         | Math reasoning                                                      |
| Model                          | Qwen2.5-1.5B-Instruct                                               |
| Rounds                         | 5                                                                   |
| Candidates / round             | 2000                                                                |
| Accepted train samples / round | 500                                                                 |
| Eval                           | GSM8K, MATH500, SVAMP                                               |
| Seeds                          | 2                                                                   |
| Baselines                      | Base, Random, Difficulty, R-Diverse-style, Ours-ELP, Ours-ELP-Atlas |

MVP 成功标准：

* Ours-ELP-Atlas final score > Difficulty baseline；
* Ours-ELP-Atlas round AUC > R-Diverse-style；
* skill coverage 更高；
* forgetting 更低；
* predicted ELP 与 actual improvement 有正相关。

---

## 10.2 主论文实验

| 设置                             | 值                                                                                                                |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Domains                        | Math + tool-use                                                                                                  |
| Models                         | 1.5B, 3B, 7B                                                                                                     |
| Rounds                         | 10                                                                                                               |
| Candidates / round             | 4000–8000                                                                                                        |
| Accepted train samples / round | 1000–2000                                                                                                        |
| Seeds                          | 3                                                                                                                |
| Baselines                      | Base, Random, Difficulty, Uncertainty, Surface Diversity, R-Diverse-style, SAGE-style, TPAW-style, Ours variants |
| Eval                           | math/general reasoning + tool-use benchmarks                                                                     |

主结果表应该按 model size 分开：

```text
Table 1: Math reasoning final performance
Table 2: Tool-use final performance
Table 3: Long-run evolution AUC
Table 4: Forgetting and skill coverage
Table 5: Cost-normalized improvement
```

---

## 10.3 长轮数实验

目标：证明不是 3 轮小提升，而是长期稳定。

| 设置                 | 值                                           |
| ------------------ | ------------------------------------------- |
| Model              | 1.5B or 3B                                  |
| Rounds             | 20                                          |
| Candidates / round | 2000                                        |
| Accepted / round   | 500                                         |
| Baselines          | Difficulty, R-Diverse-style, Ours-ELP-Atlas |
| Eval frequency     | every round                                 |

关键图：

```text
Figure 1: Benchmark accuracy vs round
Figure 2: Skill coverage vs round
Figure 3: Forgetting rate vs round
Figure 4: Candidate accept rate vs round
Figure 5: Predicted ELP vs actual improvement
```

---

# 11. 评测指标

## 11.1 主任务指标

数学 / reasoning：

```text
accuracy
pass@1
pass@k
exact match
symbolic match
```

tool-use：

```text
full call accuracy
tool selection accuracy
argument accuracy
multi-call accuracy
execution success
invalid JSON rate
invalid schema rate
```

code，可选：

```text
pass@1
pass@10
unit test pass rate
hidden test pass rate
```

---

## 11.2 长期进化指标

### Evolution AUC

[
AUC = \frac{1}{R} \sum_{r=1}^{R} Score_r
]

比 final score 更稳，因为有些方法最后一轮偶然高。

### Monotonicity

[
Mono = 1 - \frac{#{r: Score_r < Score_{r-1} - \epsilon}}{R-1}
]

### Long-run gain

[
Gain_{long} = Score_R - Score_0
]

### Collapse indicator

如果连续两轮满足以下任意条件，就标记 collapse：

```text
accept_rate < 5%
skill_entropy drops by > 30%
eval_score drops by > 3 points
invalid_task_rate > 50%
solver_format_error doubles
```

---

## 11.3 Skill Atlas 指标

### Skill coverage

[
Coverage = |{i: n_i > n_{\min}}|
]

### Skill entropy

[
H = -\sum_i p_i \log p_i
]

其中 (p_i) 是训练样本在 skill node 上的分布。

### Skill novelty

[
Novelty = 1 - \max_{m \in M} \cos(z, z_m)
]

### Diversity illusion gap

对比 surface diversity 和 skill diversity：

[
DIG = Diversity_{surface} - Diversity_{skill}
]

如果 DIG 很大，说明问题看起来多样，但底层技能重复。

---

## 11.4 ELP 质量指标

这是最重要的新指标。

### Predicted-vs-actual correlation

每轮记录：

[
\widehat{ELP}(\tau)
]

然后训练后测：

[
ActualLP(\tau)
]

计算 Spearman correlation：

[
\rho = Spearman(\widehat{ELP}, ActualLP)
]

如果 (\rho > 0)，说明 ELP reward 不是玄学。

### Top-k ELP hit rate

取 predicted ELP top 20% 样本，看它们是否真的带来更大 improvement。

```text
hit_rate = actual_lp(top_20%) > actual_lp(random_20%)
```

---

## 11.5 Forgetting 指标

维护 old memory set (M_o)。

[
Forgetting_r =
\max(0, Score_{r-1}(M_o) - Score_r(M_o))
]

报告：

```text
average forgetting
max forgetting
forgetting AUC
old skill retention
```

---

## 11.6 Cost-normalized 指标

必须报告，否则 reviewer 会质疑 ELP 太贵。

```text
score gain / generated token
score gain / training token
score gain / GPU hour
score gain / verifier call
score gain / probe update
```

---

# 12. 消融实验

## 12.1 核心模块消融

| ID  | Variant                                       | 目的                             |
| --- | --------------------------------------------- | ------------------------------ |
| A0  | Full ELP-Atlas                                | 主方法                            |
| A1  | no ELP, use difficulty only                   | 验证 ELP 价值                      |
| A2  | no Atlas, flat memory                         | 验证 Capability Atlas 价值         |
| A3  | no anti-regression                            | 验证防遗忘                          |
| A4  | no replay memory                              | 验证 replay                      |
| A5  | no skill novelty                              | 验证 skill diversity             |
| A6  | surface novelty instead of skill novelty      | 验证 skill abstraction           |
| A7  | no probe, gradient-only ELP                   | 验证 probe 是否必要                  |
| A8  | no gradient, probe-only on random subset      | 验证两阶段设计                        |
| A9  | no Planner / no solution outline              | 验证 structured skill extraction |
| A10 | fixed curriculum instead of Atlas acquisition | 验证 adaptive curriculum         |
| A11 | no historical checkpoints                     | 验证 checkpoint team 价值          |
| A12 | no noise penalty                              | 验证质量控制                         |

---

## 12.2 Reward 组件消融

完整 reward：

[
R_G =
w_1 LP
+
w_2 Frontier
+
w_3 Novelty
-----------

## w_4 Regression

## w_5 Noise

w_6 Cost
]

消融：

| Variant         | Reward            |
| --------------- | ----------------- |
| LP only         | (LP)              |
| LP + Frontier   | (LP + Frontier)   |
| LP + Novelty    | (LP + Novelty)    |
| LP - Regression | (LP - Regression) |
| LP - Noise      | (LP - Noise)      |
| Full no Cost    | 去掉 cost penalty   |
| Full            | 全部                |

关键看：

* final score；
* long-run AUC；
* forgetting；
* accept rate；
* invalid task rate；
* ELP correlation。

---

## 12.3 Atlas 设计消融

| Variant                   | 设置                           |
| ------------------------- | ---------------------------- |
| online clustering         | 默认                           |
| fixed taxonomy            | 预定义 skill taxonomy           |
| no edge transfer          | 不建 transfer edges            |
| no density penalty        | 不惩罚重复 skill                  |
| high clustering threshold | 更多细粒度节点                      |
| low clustering threshold  | 更少粗粒度节点                      |
| text embedding            | 用 problem text embedding     |
| skill-record embedding    | 用 structured skill embedding |

目标是证明 structured skill graph 比普通 embedding memory 更强。

---

## 12.4 Probe update 消融

| Variant               | 设置          |
| --------------------- | ----------- |
| probe steps = 0       | 只有 gradient |
| probe steps = 1       | 默认          |
| probe steps = 3       | 更准但更贵       |
| frontier memory = 16  | 便宜          |
| frontier memory = 64  | 默认          |
| frontier memory = 256 | 更稳          |
| old memory = 0        | 不测遗忘        |
| old memory = 128      | 默认          |
| old memory = 512      | 更稳          |

报告 trade-off：

```text
ELP correlation vs GPU cost
final score vs GPU cost
```

---

## 12.5 Solver 训练方式消融

| Variant                   | Solver update |
| ------------------------- | ------------- |
| SFT on generated solution | 便宜            |
| DPO correct vs incorrect  | 中等            |
| GRPO/RLVR                 | 默认            |
| GRPO + replay             | 默认增强          |
| GRPO no replay            | 对照            |

在 verifiable domain，主实验建议用 GRPO/RLVR，因为可以避免过度相信 Challenger 的 generated answer。

---

# 13. 公平性控制

所有方法统一：

```yaml
fairness:
  same_base_model: true
  same_total_generated_tokens: true
  same_total_solver_training_tokens: true
  same_eval_prompts: true
  same_verifier: true
  same_num_rounds: true
  same_num_random_seeds: true
  same_lora_rank_for_solver: true
  same_lora_rank_for_challenger: true
```

对 ELP-Atlas 额外 probe 的算力，要单独报告。

最好做两个 comparison：

1. **same training token budget**
   看谁训练数据更有效。

2. **same wall-clock / GPU-hour budget**
   看 ELP 的额外 probe 是否值得。

---

# 14. 自动优化方案

让 AI agent 自动调参时，不要让它直接在 test set 上调。设置 dev set。

## 14.1 Search space

```yaml
search_space:
  w_lp: [0.5, 2.0]
  w_frontier: [0.0, 1.0]
  w_novelty: [0.0, 1.0]
  w_regression: [0.2, 2.0]
  w_noise: [0.2, 2.0]
  w_cost: [0.0, 0.2]

  atlas_sampling_temperature: [0.4, 1.5]
  cluster_threshold: [0.70, 0.90]

  challenger_lr: [3.0e-6, 3.0e-5]
  solver_lr: [1.0e-6, 1.0e-5]
  challenger_kl: [0.005, 0.05]
  solver_kl: [0.005, 0.08]

  pre_eval_rollouts: [2, 4, 8]
  probe_steps: [1, 2, 3]
  frontier_memory_size: [32, 64, 128]
  old_memory_size: [64, 128, 256]

  solver_train_samples_per_round: [500, 1000, 2000]
```

## 14.2 HPO objective

[
Obj =
AUC_{dev}
+
0.5 FinalScore_{dev}
--------------------

## 0.3 Forgetting

## 0.1 InvalidRate

0.05 Cost
]

伪代码：

```python
objective = (
    eval_auc
    + 0.5 * final_eval
    - 0.3 * forgetting_auc
    - 0.1 * invalid_task_rate
    - 0.05 * normalized_gpu_cost
)
```

## 14.3 Early stopping

一个 run 满足任一条件就停：

```text
round >= 3 and eval_score drops for 2 consecutive rounds
accept_rate < 5%
invalid_task_rate > 60%
skill_entropy < 50% of round-1 value
ELP_correlation < 0 for 2 consecutive rounds
solver_format_error_rate > 30%
```

---

# 15. 结果表设计

## Table 1：主 benchmark 结果

```text
Method | GSM8K | MATH500 | SVAMP | ASDiv | BBH | Avg
Base
Random-ST
Difficulty-SP
Uncertainty-SP
Surface-Diversity
R-Diverse-style
SAGE-style
TPAW-style
Ours-ELP
Ours-Atlas
Ours-ELP-Atlas
```

## Table 2：tool-use 结果

```text
Method | Tool Select | Arg Acc | Full Call | Multi-call | Exec Success | Invalid JSON
Base
Tool-R0-style
Difficulty-SP
R-Diverse-style
Ours-ELP
Ours-ELP-Atlas
```

## Table 3：长期稳定性

```text
Method | Final | AUC | Monotonicity | Collapse? | Forgetting | Skill Entropy
Difficulty-SP
R-Diverse-style
SAGE-style
Ours-ELP-Atlas
```

## Table 4：ELP 质量

```text
Model | Domain | ELP Spearman | Top-20% Hit Rate | Probe Cost | Final Gain
1.5B | Math
3B | Math
7B | Math
1.5B | Tool
3B | Tool
```

## Table 5：消融

```text
Variant | Avg Score | AUC | Forgetting | Skill Coverage | Invalid Rate
Full
no ELP
no Atlas
no Anti-Reg
no Replay
no Skill Novelty
surface novelty
gradient-only
probe-only
fixed curriculum
```

---

# 16. 图设计

必须画这些图：

## Figure 1：self-evolution curves

x-axis：round
y-axis：average benchmark score

比较：

```text
Difficulty-SP
R-Diverse-style
SAGE-style
Ours-ELP-Atlas
```

## Figure 2：skill coverage vs round

证明 Atlas 没有陷入重复 skill。

## Figure 3：forgetting vs round

证明 anti-regression 有用。

## Figure 4：predicted ELP vs actual learning progress

scatter plot + Spearman。

这是论文最关键机制图。

## Figure 5：candidate distribution over skill graph

用 t-SNE / UMAP 展示不同方法生成数据的 skill coverage。

## Figure 6：cost-performance frontier

x-axis：GPU hours / generated tokens
y-axis：score gain

证明 ELP 额外成本值得。

---

# 17. 具体工程目录

建议项目结构：

```text
elp_atlas/
  configs/
    math_1p5b.yaml
    math_3b.yaml
    tool_1p5b.yaml
    ablation_no_elp.yaml
    ablation_no_atlas.yaml

  data/
    seeds/
    eval/
    generated/
    memory/

  elp_atlas/
    models/
      load_model.py
      lora_utils.py

    generation/
      challenger_prompts.py
      generate_candidates.py
      validate_candidates.py

    verifier/
      math_verifier.py
      symbolic_verifier.py
      tool_verifier.py
      code_verifier.py

    atlas/
      skill_abstractor.py
      skill_encoder.py
      online_cluster.py
      capability_atlas.py
      memory_bank.py

    elp/
      gradient_alignment.py
      probe_update.py
      reward.py

    training/
      train_challenger_grpo.py
      train_solver_grpo.py
      train_solver_dpo.py
      replay_sampler.py

    evaluation/
      eval_math.py
      eval_tool.py
      eval_skill_memory.py
      eval_forgetting.py
      eval_elp_correlation.py

    analysis/
      plot_curves.py
      plot_skill_graph.py
      make_tables.py

  scripts/
    run_round.py
    run_full_experiment.py
    run_ablation.py
    run_hpo.py
```

---

# 18. 关键配置文件示例

```yaml
experiment:
  name: elp_atlas_math_qwen25_3b
  domain: math
  seed: 42
  num_rounds: 10

model:
  base: Qwen2.5-3B-Instruct
  dtype: bf16
  use_lora: true

generation:
  num_target_nodes: 256
  samples_per_node: 16
  max_candidates_per_round: 4096
  max_problem_len: 1024
  max_solution_len: 1024
  temperature: 0.9
  top_p: 0.95

filter:
  require_json: true
  require_verifier: true
  max_invalid_rate: 0.5
  answer_leakage_threshold: 0.85
  min_problem_len: 20
  max_problem_len: 1000

atlas:
  cluster_threshold: 0.78
  memory_per_node: 64
  replay_per_round: 256
  frontier_competence_min: 0.25
  frontier_competence_max: 0.75
  acquisition:
    alpha_learning_progress: 1.0
    beta_uncertainty: 0.4
    gamma_frontier: 0.5
    delta_density: 0.3
    rho_forgetting: 0.6
    eta_transfer: 0.2
    temperature: 0.8

elp:
  cheap_stage:
    use_gradient_alignment: true
    top_k_per_skill: 8
  probe_stage:
    enabled: true
    probe_steps: 1
    probe_lr: 2.0e-5
    probe_group_size: 8
    frontier_memory_size: 64
    old_memory_size: 128
  reward:
    w_lp: 1.0
    w_frontier: 0.3
    w_novelty: 0.25
    w_regression: 0.7
    w_noise: 0.8
    w_cost: 0.05

challenger:
  method: grpo
  lora_rank: 32
  lr: 1.0e-5
  batch_size: 64
  rollouts_per_prompt: 8
  kl_coef: 0.02

solver:
  method: grpo
  lora_rank: 64
  lr: 5.0e-6
  batch_size: 128
  rollouts_per_task: 8
  kl_coef: 0.03
  train_samples_per_round: 1500
  include_replay: true
  replay_ratio: 0.2

eval:
  every_round: true
  benchmarks:
    - gsm8k
    - math500
    - svamp
    - asdiv
    - bbh_subset
  num_eval_rollouts: 1

logging:
  save_candidates: true
  save_atlas: true
  save_probe_stats: true
  save_grad_stats: true
  save_checkpoints_every_round: true
```

---

# 19. 错误分析设计

每轮抽样 200 个失败 case，自动分类 failure mode。

## 数学 failure modes

```json
{
  "calculation_error": 0,
  "wrong_equation": 0,
  "missing_constraint": 0,
  "entity_tracking_error": 0,
  "case_split_missing": 0,
  "unit_conversion_error": 0,
  "format_error": 0,
  "ambiguous_problem": 0,
  "wrong_reference_answer": 0
}
```

## tool-use failure modes

```json
{
  "wrong_tool": 0,
  "missing_tool_call": 0,
  "extra_tool_call": 0,
  "wrong_argument": 0,
  "missing_argument": 0,
  "extra_argument": 0,
  "wrong_call_order": 0,
  "invalid_json": 0,
  "invalid_schema": 0
}
```

Tool-R0 的实验分析本身就关注 tool selection、argument、call correctness 这类失败，因此这个错误分析和既有工作自然接轨。([arXiv][3])

---

# 20. 预期结果与判断标准

## 20.1 强结果

如果出现下面结果，论文非常 solid：

```text
Ours-ELP-Atlas > R-Diverse-style by 2–5 avg points
Ours-ELP-Atlas > Difficulty-SP by 4–8 avg points
Ours-ELP-Atlas has lower forgetting by 30–50%
ELP predicted-vs-actual Spearman > 0.25
Long-run 10-round AUC clearly better
Tool-use domain also improves
```

## 20.2 中等结果

也可以发，但要讲机制：

```text
final score only +1–2 points
but long-run stability much better
and forgetting much lower
and ELP correlation positive
```

这时论文主张应从“更强性能”转向“更稳定、更可解释的 self-evolution”。

## 20.3 危险结果

如果出现：

```text
ELP correlation <= 0
probe cost very high but gain small
skill graph coverage high yet eval 不提升
```

说明 ELP 估计不准，需要优先修：

1. verifier 噪声；
2. skill abstraction；
3. probe memory 选择；
4. Solver training stability；
5. reward 权重。

---

# 21. 常见失败与修复

## 问题 1：Challenger 生成很多 invalid tasks

修复：

```yaml
increase_noise_penalty: true
lower_temperature: 0.7
add_format_reward: true
use_stricter_json_schema: true
reject_skill_nodes_with_high_invalid_rate: true
```

## 问题 2：ELP 高但 eval 不涨

可能原因：

* probe memory 太接近训练样本；
* skill node 太细，导致局部提升不泛化；
* verifier 太弱；
* Solver update 没有真正学进去。

修复：

```yaml
increase_frontier_memory_diversity: true
lower_cluster_threshold: 0.72
add_cross_skill_memory_eval: true
increase_solver_train_epochs: 2
increase_replay_ratio: 0.3
```

## 问题 3：模型遗忘旧 skill

修复：

```yaml
increase_w_regression: 1.2
increase_replay_ratio: 0.4
increase_old_memory_size: 256
sample_high_forgetting_nodes_more_often: true
```

## 问题 4：skill graph 爆炸，节点太多

修复：

```yaml
raise_cluster_threshold? false
```

这里容易搞反。节点太多说明判定“不同 skill”的门槛太低，所以应该降低新建节点概率：

```yaml
lower_cluster_threshold: 0.72
merge_small_nodes: true
min_node_size: 5
```

## 问题 5：Challenger reward hacking

表现：

* 题目奇怪；
* answer 泄露；
* verifier 过窄；
* Solver 学会格式 trick。

修复：

```yaml
increase_noise_penalty: 1.5
add_answer_leakage_filter: true
add_verifier_fuzzing: true
cap_reward_components: true
use_reward_clipping: [-2, 2]
increase_kl_to_base: 0.05
```

---

# 22. 最推荐的执行顺序

## Phase 1：复现小 baseline

先做：

```text
Base
Random-ST
Difficulty-SP
R-Diverse-style
```

模型用 1.5B，跑 3 rounds。

目标不是追性能，是确认：

* verifier 正常；
* Generator 能产生有效任务；
* Solver 能被训练；
* eval pipeline 稳定。

---

## Phase 2：加入 ELP-only

跑：

```text
Difficulty-SP
Ours-ELP
```

看 ELP 是否比 difficulty 更好。

必须记录：

```text
predicted ELP
actual LP
ELP Spearman
probe cost
```

---

## Phase 3：加入 Atlas-only

跑：

```text
R-Diverse-style
Ours-Atlas
```

看 Capability Atlas 是否比 MAP/SAM 更能维持长期 skill coverage。

---

## Phase 4：Full ELP-Atlas

跑完整方法 5 rounds。

如果 5 rounds 有明显优势，再扩到 10 rounds 和 3 seeds。

---

## Phase 5：tool-use transfer

把同样机制迁移到 Tool-R0-style setting。

目标是证明：

```text
ELP-Atlas 不只适用于数学，也适用于 agent/tool learning。
```

---

## Phase 6：scale up

跑 3B / 7B。

这一步最后做，因为贵。

---

# 23. 最小实验命令设计

可以让 agent 执行类似：

```bash
python scripts/run_full_experiment.py \
  --config configs/math_1p5b.yaml \
  --method difficulty_sp \
  --seed 1

python scripts/run_full_experiment.py \
  --config configs/math_1p5b.yaml \
  --method r_diverse_style \
  --seed 1

python scripts/run_full_experiment.py \
  --config configs/math_1p5b.yaml \
  --method ours_elp \
  --seed 1

python scripts/run_full_experiment.py \
  --config configs/math_1p5b.yaml \
  --method ours_elp_atlas \
  --seed 1
```

消融：

```bash
python scripts/run_ablation.py \
  --base_config configs/math_3b.yaml \
  --ablation no_elp no_atlas no_regression no_replay surface_novelty gradient_only \
  --seeds 1 2 3
```

HPO：

```bash
python scripts/run_hpo.py \
  --config configs/math_1p5b.yaml \
  --method ours_elp_atlas \
  --budget_trials 40 \
  --max_rounds 5 \
  --scheduler asha
```

---

# 24. 论文中最关键的一段结论应该长这样

你要证明的不只是“分数高”，而是：

> Difficulty-based self-play asks whether a task is hard.
> Diversity-based self-play asks whether a task is different.
> ELP-Atlas asks whether a task is learnable, transferable, and non-destructive.
> This shift turns self-evolution from blind curriculum generation into online experimental design over the model’s own capability landscape.

这就是这个方向的大创新点。
如果实验做干净，这个方案的贡献会比“又加一个 agent / 又换一个 reward prompt”扎实很多。

[1]: https://arxiv.org/abs/2602.13103?utm_source=chatgpt.com "R-Diverse: Mitigating Diversity Illusion in Self-Play LLM Training"
[2]: https://arxiv.org/abs/2603.15255?utm_source=chatgpt.com "SAGE: Multi-Agent Self-Evolution for LLM Reasoning"
[3]: https://arxiv.org/abs/2602.21320?utm_source=chatgpt.com "Tool-R0: Self-Evolving LLM Agents for Tool-Learning from Zero Data"
[4]: https://arxiv.org/abs/2605.09959 "[2605.09959] G-Zero: Self-Play for Open-Ended Generation from Zero Data"
[5]: https://arxiv.org/abs/2605.09922 "[2605.09922] Team-Based Self-Play With Dual Adaptive Weighting for Fine-Tuning LLMs"
