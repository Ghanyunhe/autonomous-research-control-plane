## Promotion Gating Frontier Evolution Design

Date: 2026-05-21

### Context

`autonomous_research_campaign` already persists richer backlog and hypothesis frontier state than the earlier MVP shape:

- `campaign_backlog.frontier_history`
- `campaign_hypotheses.frontier_history`
- `movement_summary`
- `driver_snapshot`
- `pressure_snapshot`
- live backlog reselection influenced by backlog frontier pressure
- live backlog reselection influenced by linked hypothesis frontier pressure
- minimal hypothesis `tracked_reprioritization` when hypothesis challenger pressure is rising

This is materially better than pure current-snapshot state, but the remaining audit gap is still real: backlog and hypothesis evolution are still thin compared with a richer planner-backed reprioritizable evolving model. In particular, the current behavior still allows a challenger to be promoted primarily because pressure is rising, without a distinct “is it actually ready to be promoted now?” decision layer.

### Goal

Introduce a minimal `promotion gating` layer for durable-state backlog and hypothesis frontier evolution so that challenger promotion requires both:

1. frontier pressure conditions
2. lightweight readiness conditions derived from existing tracked outcome state

This should make frontier evolution behave more like a small planner-backed model while staying deterministic, explainable, and compatible with the current single-question workflow.

### Non-Goals

This design does not introduce:

- a second full scorer
- a full hypothesis/evidence graph
- a new Brain planning framework
- broader multi-worker orchestration
- cold-start first-round gating semantics
- heavyweight probabilistic promotion logic

### Recommended Approach

Use one shared minimal promotion-gating rule for:

- backlog tracked-candidate reselection
- hypothesis `tracked_reprioritization`

The rule should sit on top of already-existing pressure-aware frontier logic rather than replacing it. Pressure remains the trigger that a challenger is “pressing”; gating adds a second decision: whether that pressure is enough to justify promotion now.

This is preferred over a hypothesis-only gate because:

- the audit gap explicitly covers both backlog and hypothesis evolution
- a shared gate gives symmetric semantics
- it improves the live frontier model rather than only adding more traceability

### Design

#### 1. Promotion Gate Inputs

The gate must only use state already available in tracked backlog/hypothesis entities and frontier history:

- `challenger_pressure`
- `leader_tenure`
- `last_outcome`
- `accept_count`
- `rework_count`
- `current_accept_streak`
- `current_rework_streak`

No new scoring source is introduced.

#### 2. Pressure Preconditions

Promotion gating is only evaluated when frontier pressure already indicates a plausible challenge:

- `challenger_pressure == "rising"`
- `leader_tenure == "sustained"`

If those are not true, current behavior remains unchanged:

- no challenger promotion attempt
- no gate outcome is needed

#### 3. Gate Readiness Conditions

Once pressure preconditions are satisfied, the challenger is promotable only if it clears a lightweight readiness bar.

Minimal initial rule:

- challenger is not in obvious recent regression:
  - `last_outcome != "rework"` or `current_rework_streak == 0`
- challenger is not materially weaker than the leader on recent positive momentum:
  - `accept_count >= leader.accept_count`
  - or `current_accept_streak >= leader.current_accept_streak`

This is intentionally narrow:

- it blocks promotion for a rising-but-fragile challenger
- it still allows promotion for a challenger with credible recent momentum

#### 4. Selection Behavior

Backlog:

- pressure-aware tracked backlog reselection continues to identify a challenger
- before the challenger can outrank the leader, the promotion gate must pass
- if it fails, the leader remains selected even though pressure exists

Hypothesis:

- hypothesis `tracked_reprioritization` continues to identify a challenger hypothesis under rising pressure
- before that challenger can replace the active hypothesis leader, the promotion gate must pass
- if it fails, the active hypothesis remains on the prior leader/projection path

#### 5. Durable Explanation

Selection rationale should gain only minimal gate semantics:

- `used_promotion_gate`
- `promotion_gate_passed`
- optional `promotion_gate_blocker`

Initial blocker vocabulary:

- `challenger_recent_rework`
- `challenger_weaker_acceptance`

This keeps the system explainable without turning selection rationale into a large planner ledger.

### Data Contract Changes

#### Backlog selection rationale

When pressure-aware tracked reselection is evaluated:

- `used_promotion_gate: true`
- `promotion_gate_passed: true | false`
- `promotion_gate_blocker: <enum> | null`

#### Hypothesis selection rationale

When hypothesis `tracked_reprioritization` is evaluated:

- `used_promotion_gate: true`
- `promotion_gate_passed: true | false`
- `promotion_gate_blocker: <enum> | null`

No new top-level state structures are required for the first version.

### Error Handling and Behavioral Boundaries

- If leader or challenger streak/outcome fields are missing, the system should default conservatively:
  - do not pass promotion gate based on missing evidence alone
- Gate semantics apply only to durable-state reselection / reprioritization paths
- Cold-start backlog-file selection remains unchanged
- Recovery and continuation planning contracts are not expanded in the first implementation step unless needed to preserve truthful rationale

### Testing Strategy

Implementation is only complete when the following evidence exists:

1. State-level tests
- selection rationale persists:
  - `used_promotion_gate`
  - `promotion_gate_passed`
  - `promotion_gate_blocker`

2. CLI backlog workflow proof
- rising backlog challenger pressure exists
- challenger fails gate
- leader remains selected
- durable `selection_rationale` records gate failure

3. CLI hypothesis workflow proof
- rising hypothesis challenger pressure exists
- challenger fails gate
- hypothesis stays on previous leader/projection path
- durable rationale records gate failure

4. CLI success-path proof
- rising pressure plus qualifying challenger momentum
- gate passes
- challenger is promoted
- durable rationale records successful gate use

### Risks

Primary risk:

- overfitting the gate to current tests and making evolution too conservative

Mitigation:

- keep the initial gate minimal
- rely only on a tiny set of already-existing signals
- avoid introducing numeric weighted scoring

Secondary risk:

- accidentally widening semantics into cold-start selection or Brain routing

Mitigation:

- constrain the first implementation to durable-state reselection paths only

### Expected Outcome

After implementation, frontier evolution will be meaningfully stronger:

- a challenger is not promoted only because it is nearby and rising
- a challenger must also show minimal readiness to be promoted now
- backlog and hypothesis frontiers both gain the first real “promotion decision” layer

This should narrow the remaining expansion-readiness gap more directly than additional operator-facing traceability fields.
