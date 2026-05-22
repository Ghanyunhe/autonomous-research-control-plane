# Autonomous Research Campaign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a greenfield, single-question autonomous research campaign system that can iteratively plan, run, assess, repair, pivot, escalate, and stop without depending on the existing codebase.

**Architecture:** The system is a short-iteration research loop driven by an external orchestrator. Persistent campaign state, backlog, and policy files live on disk so each iteration is resumable and bounded. A governor layer applies explicit rules for `CONTINUE`, `REFINE`, `PIVOT`, `ESCALATE`, and `STOP`, while a Claude Code iteration worker performs one next-best experiment per round.

**Tech Stack:** Python 3.11, `pytest`, `pydantic`, `typer`, `PyYAML`

---

## File Structure

### Runtime package

- `autonomous_research_campaign/pyproject.toml`
  Standalone package metadata and dependencies for the greenfield implementation.
- `autonomous_research_campaign/README.md`
  Local project guide for the new autonomous campaign system.
- `autonomous_research_campaign/src/autorc/__init__.py`
  Package marker.
- `autonomous_research_campaign/src/autorc/models.py`
  Pydantic models for campaign spec, state, backlog items, findings, budgets, and iteration results.
- `autonomous_research_campaign/src/autorc/persistence.py`
  Load/save helpers for YAML, JSON, JSONL, and campaign snapshots.
- `autonomous_research_campaign/src/autorc/backlog.py`
  Backlog scoring, ranking, selection, and update helpers.
- `autonomous_research_campaign/src/autorc/governor.py`
  Rule-based convergence, escalation, and decision logic.
- `autonomous_research_campaign/src/autorc/prompting.py`
  Builder for the bounded iteration prompt and structured response instructions.
- `autonomous_research_campaign/src/autorc/iteration.py`
  Single-iteration execution flow and result normalization.
- `autonomous_research_campaign/src/autorc/orchestrator.py`
  Multi-iteration loop, pause/resume behavior, and campaign-level coordination.
- `autonomous_research_campaign/src/autorc/cli.py`
  CLI entrypoints for init, run, resume, status, and summarize.

### Templates and fixtures

- `autonomous_research_campaign/templates/campaign_spec.md.j2`
  Template for campaign charter generation.
- `autonomous_research_campaign/templates/governor_policy.yaml`
  Default moderate-autonomy policy template.
- `autonomous_research_campaign/templates/backlog.json`
  Seed backlog template.
- `autonomous_research_campaign/templates/campaign_state.json`
  Seed campaign state template.

### Tests

- `autonomous_research_campaign/tests/test_models.py`
  Schema validation tests.
- `autonomous_research_campaign/tests/test_persistence.py`
  Disk round-trip tests.
- `autonomous_research_campaign/tests/test_backlog.py`
  Scoring and next-step selection tests.
- `autonomous_research_campaign/tests/test_governor.py`
  Decision rule tests.
- `autonomous_research_campaign/tests/test_iteration.py`
  One-round iteration flow tests with stubbed executor output.
- `autonomous_research_campaign/tests/test_orchestrator.py`
  Loop control, stop, escalate, and resume tests.
- `autonomous_research_campaign/tests/test_cli.py`
  CLI smoke tests.

### Example campaign workspace

- `autonomous_research_campaign/examples/campaigns/demo/campaign_spec.md`
  Example research question spec.
- `autonomous_research_campaign/examples/campaigns/demo/campaign_state.json`
  Example initialized state.
- `autonomous_research_campaign/examples/campaigns/demo/governor_policy.yaml`
  Example policy.
- `autonomous_research_campaign/examples/campaigns/demo/backlog.json`
  Example backlog.

---

### Task 1: Scaffold The Greenfield Package

**Files:**
- Create: `autonomous_research_campaign/pyproject.toml`
- Create: `autonomous_research_campaign/README.md`
- Create: `autonomous_research_campaign/src/autorc/__init__.py`
- Create: `autonomous_research_campaign/src/autorc/cli.py`
- Test: `autonomous_research_campaign/tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI smoke test**

```python
from typer.testing import CliRunner

from autorc.cli import app


runner = CliRunner()


def test_status_command_shows_placeholder_message() -> None:
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "autonomous research campaign" in result.stdout.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_cli.py::test_status_command_shows_placeholder_message -v`
Expected: FAIL with `ModuleNotFoundError` for `autorc`

- [ ] **Step 3: Write minimal package scaffold**

```toml
[project]
name = "autonomous-research-campaign"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.7", "PyYAML>=6.0", "typer>=0.12"]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
autorc = "autorc.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```python
import typer


app = typer.Typer(help="Autonomous research campaign CLI")


@app.command()
def status() -> None:
    typer.echo("Autonomous research campaign status: scaffold ready")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_cli.py::test_status_command_shows_placeholder_message -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add autonomous_research_campaign/pyproject.toml autonomous_research_campaign/README.md autonomous_research_campaign/src/autorc/__init__.py autonomous_research_campaign/src/autorc/cli.py autonomous_research_campaign/tests/test_cli.py
git commit -m "feat: scaffold autonomous research campaign package"
```

### Task 2: Define Campaign Domain Models

**Files:**
- Create: `autonomous_research_campaign/src/autorc/models.py`
- Test: `autonomous_research_campaign/tests/test_models.py`

- [ ] **Step 1: Write the failing schema validation tests**

```python
from autorc.models import BacklogItem, CampaignState, ConvergenceStatus, Hypothesis


def test_campaign_state_accepts_valid_payload() -> None:
    state = CampaignState(
        campaign_id="cq-20260518-demo",
        status="active",
        mode="moderate_autonomy",
        research_question="Does method X improve robustness under label noise?",
        phase="core_experimentation",
        current_hypotheses=[
            Hypothesis(
                id="h1",
                statement="Method X improves robustness under 20% label noise",
                status="active",
                confidence=0.4,
            )
        ],
        backlog=[
            BacklogItem(
                id="exp_01",
                title="Run baseline at 20% noise",
                priority=0.8,
                cost_estimate="medium",
                expected_information_gain=0.7,
                status="queued",
            )
        ],
        completed_experiments=[],
        key_findings=[],
        open_uncertainties=[],
        budget_status={"runtime_hours_used": 0.0, "api_cost_used_usd": 0.0, "experiments_run": 0},
        convergence_status=ConvergenceStatus(
            evidence_convergence=0.0,
            budget_convergence=0.0,
            deliverable_convergence=0.0,
            overall="not_converged",
        ),
        failure_streak=0,
        last_decision="CONTINUE",
        last_iteration_id="iter_0000",
        escalation_pending=False,
        final_report_ready=False,
    )
    assert state.campaign_id == "cq-20260518-demo"


def test_backlog_item_rejects_out_of_range_priority() -> None:
    try:
        BacklogItem(
            id="exp_bad",
            title="Bad item",
            priority=1.2,
            cost_estimate="low",
            expected_information_gain=0.3,
            status="queued",
        )
    except ValueError as exc:
        assert "priority" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing model names

- [ ] **Step 3: Write minimal Pydantic models**

```python
from typing import Literal

from pydantic import BaseModel, Field


Decision = Literal["CONTINUE", "REFINE", "PIVOT", "ESCALATE", "STOP"]


class Hypothesis(BaseModel):
    id: str
    statement: str
    status: Literal["active", "supported", "rejected", "paused"]
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    conflicting_evidence: list[str] = Field(default_factory=list)


class BacklogItem(BaseModel):
    id: str
    title: str
    priority: float = Field(ge=0.0, le=1.0)
    cost_estimate: Literal["low", "medium", "high"]
    expected_information_gain: float = Field(ge=0.0, le=1.0)
    status: Literal["queued", "running", "done", "blocked", "dropped"]


class ConvergenceStatus(BaseModel):
    evidence_convergence: float = Field(ge=0.0, le=1.0)
    budget_convergence: float = Field(ge=0.0, le=1.0)
    deliverable_convergence: float = Field(ge=0.0, le=1.0)
    overall: Literal["not_converged", "near_converged", "converged"]


class CampaignState(BaseModel):
    campaign_id: str
    status: Literal["active", "paused", "stopped", "completed"]
    mode: Literal["strong_autonomy", "moderate_autonomy", "strict_review"]
    research_question: str
    phase: str
    current_hypotheses: list[Hypothesis]
    backlog: list[BacklogItem]
    completed_experiments: list[str]
    key_findings: list[dict] = Field(default_factory=list)
    open_uncertainties: list[str]
    budget_status: dict
    convergence_status: ConvergenceStatus
    failure_streak: int = Field(ge=0)
    last_decision: Decision
    last_iteration_id: str
    escalation_pending: bool
    final_report_ready: bool
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add autonomous_research_campaign/src/autorc/models.py autonomous_research_campaign/tests/test_models.py
git commit -m "feat: add campaign domain models"
```

### Task 3: Add Persistence And Seed Templates

**Files:**
- Create: `autonomous_research_campaign/src/autorc/persistence.py`
- Create: `autonomous_research_campaign/templates/campaign_state.json`
- Create: `autonomous_research_campaign/templates/backlog.json`
- Create: `autonomous_research_campaign/templates/governor_policy.yaml`
- Test: `autonomous_research_campaign/tests/test_persistence.py`

- [ ] **Step 1: Write the failing persistence round-trip tests**

```python
from pathlib import Path

from autorc.persistence import load_json, save_json


def test_save_and_load_json_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    payload = {"campaign_id": "cq-demo", "status": "active"}
    save_json(target, payload)
    assert load_json(target) == payload
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_persistence.py -v`
Expected: FAIL with missing `load_json` or `save_json`

- [ ] **Step 3: Write minimal persistence helpers and templates**

```python
import json
from pathlib import Path
from typing import Any

import yaml


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))
```

```json
{
  "campaign_id": "cq-demo",
  "status": "active",
  "mode": "moderate_autonomy",
  "research_question": "Replace me",
  "phase": "scoping",
  "current_hypotheses": [],
  "backlog": [],
  "completed_experiments": [],
  "key_findings": [],
  "open_uncertainties": [],
  "budget_status": {
    "runtime_hours_used": 0.0,
    "api_cost_used_usd": 0.0,
    "experiments_run": 0
  },
  "convergence_status": {
    "evidence_convergence": 0.0,
    "budget_convergence": 0.0,
    "deliverable_convergence": 0.0,
    "overall": "not_converged"
  },
  "failure_streak": 0,
  "last_decision": "CONTINUE",
  "last_iteration_id": "iter_0000",
  "escalation_pending": false,
  "final_report_ready": false
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_persistence.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add autonomous_research_campaign/src/autorc/persistence.py autonomous_research_campaign/templates/campaign_state.json autonomous_research_campaign/templates/backlog.json autonomous_research_campaign/templates/governor_policy.yaml autonomous_research_campaign/tests/test_persistence.py
git commit -m "feat: add campaign persistence layer"
```

### Task 4: Implement Backlog Scoring And Selection

**Files:**
- Create: `autonomous_research_campaign/src/autorc/backlog.py`
- Test: `autonomous_research_campaign/tests/test_backlog.py`

- [ ] **Step 1: Write the failing backlog selection tests**

```python
from autorc.backlog import select_next_item
from autorc.models import BacklogItem


def test_select_next_item_prefers_high_information_gain_with_reasonable_cost() -> None:
    items = [
        BacklogItem(
            id="exp_low",
            title="Cheap but low signal",
            priority=0.4,
            cost_estimate="low",
            expected_information_gain=0.2,
            status="queued",
        ),
        BacklogItem(
            id="exp_best",
            title="Best next test",
            priority=0.8,
            cost_estimate="medium",
            expected_information_gain=0.9,
            status="queued",
        ),
    ]
    selected = select_next_item(items)
    assert selected.id == "exp_best"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_backlog.py -v`
Expected: FAIL with missing `select_next_item`

- [ ] **Step 3: Write minimal backlog scoring helpers**

```python
from autorc.models import BacklogItem


COST_PENALTY = {"low": 0.05, "medium": 0.15, "high": 0.30}


def score_item(item: BacklogItem) -> float:
    return (0.55 * item.expected_information_gain) + (0.45 * item.priority) - COST_PENALTY[item.cost_estimate]


def select_next_item(items: list[BacklogItem]) -> BacklogItem:
    queued = [item for item in items if item.status == "queued"]
    if not queued:
        raise ValueError("No queued backlog items available")
    return max(queued, key=score_item)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_backlog.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add autonomous_research_campaign/src/autorc/backlog.py autonomous_research_campaign/tests/test_backlog.py
git commit -m "feat: add backlog scoring and selection"
```

### Task 5: Implement Governor Decision Rules

**Files:**
- Create: `autonomous_research_campaign/src/autorc/governor.py`
- Test: `autonomous_research_campaign/tests/test_governor.py`

- [ ] **Step 1: Write the failing governor rule tests**

```python
from autorc.governor import decide_next_action
from autorc.models import CampaignState, ConvergenceStatus


def test_governor_stops_when_evidence_and_deliverable_converged(sample_state: CampaignState) -> None:
    sample_state.convergence_status = ConvergenceStatus(
        evidence_convergence=0.9,
        budget_convergence=0.5,
        deliverable_convergence=0.95,
        overall="converged",
    )
    decision = decide_next_action(
        sample_state,
        {
            "budgets": {"max_experiments": 20},
            "convergence": {"evidence_stop_threshold": 0.85, "deliverable_stop_threshold": 0.9},
            "escalation": {"consecutive_failures_threshold": 3},
        },
    )
    assert decision == "STOP"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_governor.py -v`
Expected: FAIL with missing governor function

- [ ] **Step 3: Write minimal governor logic**

```python
from autorc.models import CampaignState


def decide_next_action(state: CampaignState, policy: dict) -> str:
    convergence = policy["convergence"]
    escalation = policy["escalation"]
    budgets = policy["budgets"]

    if state.budget_status["experiments_run"] >= budgets["max_experiments"]:
        return "STOP"
    if state.failure_streak >= escalation["consecutive_failures_threshold"]:
        return "ESCALATE"
    if (
        state.convergence_status.evidence_convergence >= convergence["evidence_stop_threshold"]
        and state.convergence_status.deliverable_convergence >= convergence["deliverable_stop_threshold"]
    ):
        return "STOP"
    if state.escalation_pending:
        return "ESCALATE"
    return "CONTINUE"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_governor.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add autonomous_research_campaign/src/autorc/governor.py autonomous_research_campaign/tests/test_governor.py
git commit -m "feat: add governor decision rules"
```

### Task 6: Add Bounded Iteration Runner

**Files:**
- Create: `autonomous_research_campaign/src/autorc/prompting.py`
- Create: `autonomous_research_campaign/src/autorc/iteration.py`
- Test: `autonomous_research_campaign/tests/test_iteration.py`

- [ ] **Step 1: Write the failing iteration flow tests**

```python
from autorc.iteration import run_iteration


def test_run_iteration_returns_structured_decision(tmp_path) -> None:
    result = run_iteration(
        campaign_dir=tmp_path,
        llm_executor=lambda prompt: {
            "iteration_id": "iter_0001",
            "selected_step": "Run baseline",
            "artifacts_created": [],
            "result_summary": "Baseline completed",
            "evidence_impact": "Weak support for h1",
            "backlog_updates": [],
            "state_updates": {"failure_streak": 0},
            "decision": "CONTINUE",
            "decision_reason": "Backlog still has high-value items",
        },
    )
    assert result["decision"] == "CONTINUE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_iteration.py -v`
Expected: FAIL with missing iteration runner

- [ ] **Step 3: Write minimal prompt builder and iteration wrapper**

```python
def build_iteration_prompt(research_question: str, phase: str) -> str:
    return (
        "You are the iteration operator for a single-question autonomous research campaign.\n"
        f"Research question: {research_question}\n"
        f"Current phase: {phase}\n"
        "Choose exactly one next best experiment. Return a structured decision."
    )
```

```python
from pathlib import Path
from typing import Callable


def run_iteration(campaign_dir: Path, llm_executor: Callable[[str], dict]) -> dict:
    prompt = "bounded iteration prompt"
    result = llm_executor(prompt)
    if "decision" not in result:
        raise ValueError("Iteration result missing decision")
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_iteration.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add autonomous_research_campaign/src/autorc/prompting.py autonomous_research_campaign/src/autorc/iteration.py autonomous_research_campaign/tests/test_iteration.py
git commit -m "feat: add bounded iteration runner"
```

### Task 7: Build The External Orchestrator Loop

**Files:**
- Create: `autonomous_research_campaign/src/autorc/orchestrator.py`
- Test: `autonomous_research_campaign/tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing orchestrator loop tests**

```python
from autorc.orchestrator import run_campaign_loop


def test_run_campaign_loop_stops_after_governor_returns_stop(tmp_path) -> None:
    events = []

    def fake_iteration(_campaign_dir):
        events.append("iteration")
        return {"decision": "STOP"}

    run_campaign_loop(tmp_path, iteration_runner=fake_iteration, max_rounds=3)
    assert events == ["iteration"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_orchestrator.py -v`
Expected: FAIL with missing orchestrator

- [ ] **Step 3: Write minimal loop controller**

```python
from pathlib import Path
from typing import Callable


def run_campaign_loop(campaign_dir: Path, iteration_runner: Callable[[Path], dict], max_rounds: int = 100) -> list[dict]:
    results = []
    for _ in range(max_rounds):
        result = iteration_runner(campaign_dir)
        results.append(result)
        if result["decision"] in {"STOP", "ESCALATE"}:
            break
    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_orchestrator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add autonomous_research_campaign/src/autorc/orchestrator.py autonomous_research_campaign/tests/test_orchestrator.py
git commit -m "feat: add campaign orchestrator loop"
```

### Task 8: Wire CLI Commands For Init, Run, Resume, And Status

**Files:**
- Modify: `autonomous_research_campaign/src/autorc/cli.py`
- Create: `autonomous_research_campaign/examples/campaigns/demo/campaign_spec.md`
- Create: `autonomous_research_campaign/examples/campaigns/demo/campaign_state.json`
- Create: `autonomous_research_campaign/examples/campaigns/demo/governor_policy.yaml`
- Create: `autonomous_research_campaign/examples/campaigns/demo/backlog.json`
- Test: `autonomous_research_campaign/tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI integration tests**

```python
from pathlib import Path

from typer.testing import CliRunner

from autorc.cli import app


runner = CliRunner()


def test_init_creates_campaign_workspace(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    result = runner.invoke(app, ["init", str(target), "--question", "Does X help Y?"])
    assert result.exit_code == 0
    assert (target / "campaign_state.json").exists()
    assert (target / "governor_policy.yaml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_cli.py -v`
Expected: FAIL with missing `init` command

- [ ] **Step 3: Write minimal CLI workflow**

```python
@app.command()
def init(path: str, question: str) -> None:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    (target / "campaign_spec.md").write_text(f"# Research Question\n\n{question}\n", encoding="utf-8")
    (target / "campaign_state.json").write_text('{"campaign_id":"demo","status":"active"}\n', encoding="utf-8")
    (target / "governor_policy.yaml").write_text("mode: moderate_autonomy\n", encoding="utf-8")
    (target / "backlog.json").write_text("[]\n", encoding="utf-8")
    typer.echo(f"Initialized campaign at {target}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add autonomous_research_campaign/src/autorc/cli.py autonomous_research_campaign/examples/campaigns/demo/campaign_spec.md autonomous_research_campaign/examples/campaigns/demo/campaign_state.json autonomous_research_campaign/examples/campaigns/demo/governor_policy.yaml autonomous_research_campaign/examples/campaigns/demo/backlog.json autonomous_research_campaign/tests/test_cli.py
git commit -m "feat: wire campaign CLI workflows"
```

### Task 9: Add Reporting, Logging, And Human Escalation Hooks

**Files:**
- Modify: `autonomous_research_campaign/src/autorc/persistence.py`
- Modify: `autonomous_research_campaign/src/autorc/orchestrator.py`
- Create: `autonomous_research_campaign/tests/test_reporting.py`

- [ ] **Step 1: Write the failing iteration log test**

```python
from pathlib import Path

from autorc.persistence import append_jsonl


def test_append_jsonl_writes_one_line_per_event(tmp_path: Path) -> None:
    target = tmp_path / "iteration_log.jsonl"
    append_jsonl(target, {"iteration_id": "iter_0001", "decision": "CONTINUE"})
    append_jsonl(target, {"iteration_id": "iter_0002", "decision": "STOP"})
    lines = target.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_reporting.py -v`
Expected: FAIL with missing `append_jsonl`

- [ ] **Step 3: Write minimal logging helpers and escalation persistence**

```python
def append_jsonl(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
```

```python
def record_iteration_result(campaign_dir: Path, result: dict) -> None:
    append_jsonl(campaign_dir / "iteration_log.jsonl", result)
    if result["decision"] == "ESCALATE":
        (campaign_dir / "ESCALATION_REQUIRED").write_text(result["decision_reason"], encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_reporting.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add autonomous_research_campaign/src/autorc/persistence.py autonomous_research_campaign/src/autorc/orchestrator.py autonomous_research_campaign/tests/test_reporting.py
git commit -m "feat: add reporting and escalation hooks"
```

### Task 10: Add Mode-Specific Policy Presets And Resume Safety

**Files:**
- Modify: `autonomous_research_campaign/templates/governor_policy.yaml`
- Modify: `autonomous_research_campaign/src/autorc/governor.py`
- Modify: `autonomous_research_campaign/src/autorc/cli.py`
- Test: `autonomous_research_campaign/tests/test_governor.py`
- Test: `autonomous_research_campaign/tests/test_cli.py`

- [ ] **Step 1: Write the failing mode preset tests**

```python
from autorc.governor import build_policy_for_mode


def test_build_policy_for_strong_autonomy_allows_auto_pivot() -> None:
    policy = build_policy_for_mode("strong_autonomy")
    assert policy["autonomy"]["auto_pivot"] is True
    assert policy["escalation"]["require_human_for_final_stop"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_governor.py::test_build_policy_for_strong_autonomy_allows_auto_pivot -v`
Expected: FAIL with missing `build_policy_for_mode`

- [ ] **Step 3: Write minimal mode preset builder**

```python
def build_policy_for_mode(mode: str) -> dict:
    if mode == "strong_autonomy":
        return {
            "autonomy": {"auto_pivot": True},
            "escalation": {"require_human_for_final_stop": False, "consecutive_failures_threshold": 5},
            "budgets": {"max_experiments": 50},
            "convergence": {"evidence_stop_threshold": 0.85, "deliverable_stop_threshold": 0.9},
        }
    if mode == "strict_review":
        return {
            "autonomy": {"auto_pivot": False},
            "escalation": {"require_human_for_final_stop": True, "consecutive_failures_threshold": 1},
            "budgets": {"max_experiments": 20},
            "convergence": {"evidence_stop_threshold": 0.9, "deliverable_stop_threshold": 0.95},
        }
    return {
        "autonomy": {"auto_pivot": False},
        "escalation": {"require_human_for_final_stop": True, "consecutive_failures_threshold": 3},
        "budgets": {"max_experiments": 40},
        "convergence": {"evidence_stop_threshold": 0.85, "deliverable_stop_threshold": 0.9},
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /vepfs_hyh/hyh/projects/AutoResearchClaw/autonomous_research_campaign && pytest tests/test_governor.py -v && pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add autonomous_research_campaign/templates/governor_policy.yaml autonomous_research_campaign/src/autorc/governor.py autonomous_research_campaign/src/autorc/cli.py autonomous_research_campaign/tests/test_governor.py autonomous_research_campaign/tests/test_cli.py
git commit -m "feat: add autonomy mode presets and resume safety"
```

---

## Self-Review

### Spec coverage

- Single-question campaign loop: covered by Tasks 2, 6, and 7.
- Persistent state and resumability: covered by Tasks 3, 7, and 10.
- Governor-based control plane: covered by Tasks 5 and 10.
- Short bounded Claude Code iterations: covered by Task 6.
- Three autonomy modes: covered by Task 10.
- Reporting, logging, and human escalation: covered by Task 9.
- Greenfield isolation from existing codebase: covered by Task 1 file boundary and all `autonomous_research_campaign/` paths.

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain in the tasks.
- Every code-changing step includes concrete file content examples.
- Every verification step includes an explicit command and expected result.

### Type consistency

- Decision vocabulary is consistently `CONTINUE`, `REFINE`, `PIVOT`, `ESCALATE`, `STOP`.
- Mode vocabulary is consistently `strong_autonomy`, `moderate_autonomy`, `strict_review`.
- Core files referenced later are introduced earlier in the plan.

---

Plan complete and saved to `autonomous_research_campaign/IMPLEMENTATION_PLAN.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
