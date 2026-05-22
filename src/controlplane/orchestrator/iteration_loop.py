from __future__ import annotations

from controlplane.dispatcher.router import resolve_launcher_for_task


def _normalize_task(task: dict, campaign_dir) -> dict:
    normalized = dict(task)
    context_refs = dict(normalized.get("context_refs", {}))
    context_refs.setdefault("repo_path", str(campaign_dir))
    normalized["context_refs"] = context_refs
    return normalized


def _launch_task(launcher, task: dict) -> dict:
    if callable(launcher):
        return launcher(task)
    return launcher.launch(task)


def _aggregate_deliverable_paths(task_results: list[dict]) -> list[str]:
    aggregated: list[str] = []
    for result in task_results:
        for path in result.get("deliverable_paths", []):
            if path not in aggregated:
                aggregated.append(path)
    return aggregated


def _aggregate_execution_summary(task_results: list[dict]) -> str:
    summaries: list[str] = []
    for result in task_results:
        summary = (result.get("summary") or "").strip()
        if summary:
            summaries.append(summary)
    return "\n".join(summaries)


def run_iteration(campaign_dir, planner, decomposer, launcher, verifier, governor, launcher_factory=None, initial_state=None):
    state = initial_state or {"budget_status": {"experiments_run": 0}, "failure_status": {"failure_streak": 0}}
    policy = {}
    brief = planner(state, policy)
    tasks = decomposer(brief)
    last_result = None
    task_results: list[dict] = []
    for task in tasks:
        normalized_task = _normalize_task(task, campaign_dir)
        active_launcher = launcher
        if active_launcher is None:
            factory = launcher_factory or resolve_launcher_for_task
            active_launcher = factory(normalized_task)
        last_result = _launch_task(active_launcher, normalized_task)
        task_results.append(last_result)
    artifacts = {
        "deliverable_paths": _aggregate_deliverable_paths(task_results),
        "execution_summary": _aggregate_execution_summary(task_results),
        "task_results": task_results,
    }
    verification = verifier(brief, artifacts, last_result)
    return governor(state, verification, policy)
