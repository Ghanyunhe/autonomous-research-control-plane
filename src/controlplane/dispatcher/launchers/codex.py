from __future__ import annotations

import subprocess

from controlplane.dispatcher.launchers.base import BaseLauncher


class CodexLauncher(BaseLauncher):
    def __init__(self, *, binary_path: str = "codex", timeout_sec: int = 300, runner=None) -> None:
        super().__init__(binary_path=binary_path, timeout_sec=timeout_sec, runner=runner)

    @staticmethod
    def build_prompt(task_packet: dict) -> str:
        goal = task_packet.get("goal", "Complete the assigned task.")
        deliverables = "\n".join(f"- {item}" for item in task_packet.get("deliverables", []))
        acceptance = "\n".join(f"- {item}" for item in task_packet.get("acceptance_criteria", []))
        return (
            "You are executing a bounded research control-plane task.\n\n"
            f"GOAL:\n{goal}\n\n"
            f"DELIVERABLES:\n{deliverables or '- none declared'}\n\n"
            f"ACCEPTANCE CRITERIA:\n{acceptance or '- none declared'}\n\n"
            "Work only within the provided repository directory. Modify only what is needed to satisfy the task."
        )

    def build_command(self, task_packet: dict) -> list[str]:
        repo_path = self._resolve_repo_path(task_packet)
        prompt = self.build_prompt(task_packet)
        return [
            self.binary_path,
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "danger-full-access",
            "--ask-for-approval",
            "never",
            "--cd",
            str(repo_path),
            prompt,
        ]

    def launch(self, task_packet: dict) -> dict:
        repo_path = self._resolve_repo_path(task_packet)
        cmd = self.build_command(task_packet)
        try:
            completed = self.runner(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "task_id": task_packet["task_id"],
                "worker_id": "codex",
                "status": "failed",
                "deliverable_paths": [
                    path for path in task_packet.get("deliverables", []) if (repo_path / path).exists()
                ],
                "summary": f"Codex launcher timed out after {self.timeout_sec} seconds",
            }
        except OSError as exc:
            return {
                "task_id": task_packet["task_id"],
                "worker_id": "codex",
                "status": "failed",
                "deliverable_paths": [
                    path for path in task_packet.get("deliverables", []) if (repo_path / path).exists()
                ],
                "summary": f"Codex launcher failed to start: {exc}",
            }
        deliverables = [
            path for path in task_packet.get("deliverables", []) if (repo_path / path).exists()
        ]
        status = "success" if completed.returncode == 0 else "failed"
        return {
            "task_id": task_packet["task_id"],
            "worker_id": "codex",
            "status": status,
            "deliverable_paths": deliverables,
            "summary": (completed.stdout or completed.stderr or "").strip() or "Codex launcher finished",
        }
