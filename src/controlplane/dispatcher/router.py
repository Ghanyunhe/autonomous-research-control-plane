from __future__ import annotations

from controlplane.dispatcher.launchers.claude_code import ClaudeCodeLauncher
from controlplane.dispatcher.launchers.codex import CodexLauncher


DEFAULT_WORKER_REGISTRY = [
    {
        "worker_id": "claude_code_primary",
        "backend": "claude_code",
        "enabled": True,
        "strengths": ["coding", "debugging", "repo_navigation"],
        "skills": ["scientific_review", "debugging", "repo_write", "experiment_execution"],
        "trusted_for": ["code_and_run", "repair", "analysis"],
    },
    {
        "worker_id": "codex_secondary",
        "backend": "codex",
        "enabled": True,
        "strengths": ["coding", "debugging", "repo_navigation"],
        "skills": ["scientific_review", "debugging", "repo_write", "experiment_execution"],
        "trusted_for": ["code_and_run", "analysis", "repair"],
    },
]


def enabled_workers(registry: list[dict]) -> list[dict]:
    return [worker for worker in registry if worker.get("enabled", False)]


def choose_worker(task_packet: dict, registry: list[dict]) -> dict:
    candidates = enabled_workers(registry)
    task_type = task_packet["task_type"]
    worker_requirements = task_packet.get("worker_requirements", {})
    preferred_backend = worker_requirements.get("backend")
    required_skills = list(worker_requirements.get("skills") or [])

    if required_skills:
        skilled_candidates = [
            worker
            for worker in candidates
            if all(skill in worker.get("skills", []) for skill in required_skills)
        ]
        if not skilled_candidates:
            raise ValueError(
                f"No worker available for task_type={task_type} with required skills={required_skills}"
            )
        candidates = skilled_candidates

    if preferred_backend and preferred_backend != "any":
        for worker in candidates:
            if worker.get("backend") == preferred_backend and task_type in worker.get("trusted_for", []):
                return worker

    if task_type == "repair":
        for worker in candidates:
            if "debugging" in worker.get("strengths", []) and task_type in worker.get("trusted_for", []):
                return worker
    for worker in candidates:
        if task_type in worker.get("trusted_for", []):
            return worker
    raise ValueError(f"No worker available for task_type={task_type}")


def create_launcher(worker: dict):
    backend = worker["backend"]
    if backend == "claude_code":
        return ClaudeCodeLauncher()
    if backend == "codex":
        return CodexLauncher()
    raise ValueError(f"Unsupported worker backend: {backend}")


def resolve_launcher_for_task(task_packet: dict, registry: list[dict] | None = None):
    selected = choose_worker(task_packet, registry or DEFAULT_WORKER_REGISTRY)
    return create_launcher(selected)
