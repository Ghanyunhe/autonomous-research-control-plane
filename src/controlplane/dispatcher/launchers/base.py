from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable


class BaseLauncher(ABC):
    def __init__(
        self,
        *,
        binary_path: str,
        timeout_sec: int = 300,
        runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self.binary_path = binary_path
        self.timeout_sec = timeout_sec
        self.runner = runner or subprocess.run

    @staticmethod
    def _resolve_repo_path(task_packet: dict) -> Path:
        context = task_packet.get("context_refs", {})
        repo_path = context.get("repo_path", ".")
        return Path(repo_path)

    @abstractmethod
    def launch(self, task_packet: dict) -> dict:
        raise NotImplementedError
