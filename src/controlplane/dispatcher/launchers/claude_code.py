from __future__ import annotations

import os
import pwd
import subprocess
from pathlib import Path

from controlplane.dispatcher.launchers.base import BaseLauncher


class ClaudeCodeLauncher(BaseLauncher):
    @staticmethod
    def _default_non_root_identity() -> tuple[str | None, str | None]:
        if os.geteuid() != 0:
            return None, None
        try:
            entry = pwd.getpwnam("ccbagent")
        except KeyError:
            return None, None
        return "ccbagent", entry.pw_dir

    def __init__(
        self,
        *,
        binary_path: str = "ccb",
        timeout_sec: int = 300,
        runner=None,
        run_as_user: str | None = None,
        home_dir: str | None = None,
    ) -> None:
        super().__init__(binary_path=binary_path, timeout_sec=timeout_sec, runner=runner)
        default_user, default_home = self._default_non_root_identity()
        self.run_as_user = run_as_user if run_as_user is not None else default_user
        self.home_dir = home_dir if home_dir is not None else default_home

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
            "-p",
            prompt,
            "--output-format",
            "text",
            "--permission-mode",
            "bypassPermissions",
            "--allowed-tools",
            "Bash,Read,Write,Edit",
            "--add-dir",
            str(repo_path),
        ]

    def wrap_command_for_execution(self, command: list[str]) -> list[str]:
        if not self.run_as_user:
            return command
        wrapped = ["runuser", "-u", self.run_as_user, "--"]
        if self.home_dir:
            wrapped.extend(["env", f"HOME={self.home_dir}"])
        wrapped.extend(command)
        return wrapped

    @staticmethod
    def _collect_deliverables(repo_path: Path, declared: list[str]) -> list[str]:
        found: list[str] = []
        for rel in declared:
            if (repo_path / rel).exists():
                found.append(rel)
        return found

    def launch(self, task_packet: dict) -> dict:
        repo_path = self._resolve_repo_path(task_packet)
        cmd = self.wrap_command_for_execution(self.build_command(task_packet))
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
                "worker_id": "claude_code",
                "status": "failed",
                "deliverable_paths": self._collect_deliverables(repo_path, task_packet.get("deliverables", [])),
                "summary": f"Claude Code launcher timed out after {self.timeout_sec} seconds",
            }
        deliverables = self._collect_deliverables(repo_path, task_packet.get("deliverables", []))
        status = "success" if completed.returncode == 0 else "failed"
        return {
            "task_id": task_packet["task_id"],
            "worker_id": "claude_code",
            "status": status,
            "deliverable_paths": deliverables,
            "summary": (completed.stdout or completed.stderr or "").strip() or "Claude Code launcher finished",
        }
