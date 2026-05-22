from __future__ import annotations

import os
import pwd
import subprocess
from pathlib import Path
from unittest.mock import patch

from controlplane.dispatcher.launchers.claude_code import ClaudeCodeLauncher
from controlplane.dispatcher.launchers.codex import CodexLauncher
from controlplane.schemas.worker_result import WorkerResult
from controlplane.schemas.verification_report import VerificationReport


def test_claude_code_launcher_builds_ccb_command(tmp_path: Path) -> None:
    launcher = ClaudeCodeLauncher(binary_path="/usr/bin/ccb")
    task = {
        "task_id": "task_1",
        "goal": "Implement the experiment runner",
        "deliverables": ["metrics.json"],
        "acceptance_criteria": ["metrics.json exists"],
        "context_refs": {"repo_path": str(tmp_path)},
    }
    cmd = launcher.build_command(task)
    assert cmd[0] == "/usr/bin/ccb"
    assert "-p" in cmd
    assert "--permission-mode" in cmd
    assert "bypassPermissions" in cmd
    assert "--add-dir" in cmd
    assert str(tmp_path) in cmd


def test_claude_code_launcher_wraps_command_for_non_root_execution(tmp_path: Path) -> None:
    launcher = ClaudeCodeLauncher(
        binary_path="/usr/bin/ccb",
        run_as_user="nobody",
        home_dir="/tmp/ccb-home",
    )
    task = {
        "task_id": "task_1",
        "goal": "Implement the experiment runner",
        "deliverables": ["metrics.json"],
        "acceptance_criteria": ["metrics.json exists"],
        "context_refs": {"repo_path": str(tmp_path)},
    }
    wrapped = launcher.wrap_command_for_execution(launcher.build_command(task))
    assert wrapped[:4] == ["runuser", "-u", "nobody", "--"]
    assert "HOME=/tmp/ccb-home" in wrapped
    assert "/usr/bin/ccb" in wrapped


def test_claude_code_launcher_auto_selects_ccbagent_when_root() -> None:
    fake_pwd = pwd.struct_passwd(("ccbagent", "x", 1000, 1000, "", "/home/ccbagent", "/bin/bash"))
    with patch.object(os, "geteuid", return_value=0), patch.object(pwd, "getpwnam", return_value=fake_pwd):
        launcher = ClaudeCodeLauncher(binary_path="/usr/bin/ccb")
    assert launcher.run_as_user == "ccbagent"
    assert launcher.home_dir == "/home/ccbagent"


def test_claude_code_launcher_returns_success_from_runner(tmp_path: Path) -> None:
    deliverable = tmp_path / "metrics.json"
    deliverable.write_text("{}", encoding="utf-8")

    def fake_runner(command, *, cwd, capture_output, text, timeout, check):  # noqa: ANN001
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    launcher = ClaudeCodeLauncher(binary_path="/usr/bin/ccb", runner=fake_runner)
    result = launcher.launch(
        {
            "task_id": "task_1",
            "goal": "Implement the experiment runner",
            "deliverables": ["metrics.json"],
            "acceptance_criteria": ["metrics.json exists"],
            "context_refs": {"repo_path": str(tmp_path)},
        }
    )
    assert result["worker_id"] == "claude_code"
    assert result["status"] == "success"
    assert result["deliverable_paths"] == ["metrics.json"]


def test_codex_launcher_returns_failed_result_when_binary_execution_fails() -> None:
    launcher = CodexLauncher(binary_path="/definitely/missing/codex")
    result = launcher.launch(
        {
            "task_id": "task_2",
            "deliverables": ["run.log"],
            "acceptance_criteria": [],
            "context_refs": {"repo_path": "."},
        }
    )
    assert result["worker_id"] == "codex"
    assert result["status"] == "failed"


def test_codex_launcher_builds_exec_command(tmp_path: Path) -> None:
    launcher = CodexLauncher(binary_path="/usr/bin/codex")
    task = {
        "task_id": "task_2",
        "goal": "Review the scientific evidence and update result_note.md",
        "deliverables": ["result_note.md"],
        "acceptance_criteria": ["result_note.md exists"],
        "context_refs": {"repo_path": str(tmp_path)},
    }

    cmd = launcher.build_command(task)

    assert cmd[:2] == ["/usr/bin/codex", "exec"]
    assert "--skip-git-repo-check" in cmd
    assert "--sandbox" in cmd
    assert "danger-full-access" in cmd
    assert str(tmp_path) in cmd


def test_codex_launcher_returns_success_from_runner(tmp_path: Path) -> None:
    deliverable = tmp_path / "result_note.md"
    deliverable.write_text("summary", encoding="utf-8")

    def fake_runner(command, *, cwd, capture_output, text, timeout, check):  # noqa: ANN001
        return subprocess.CompletedProcess(command, 0, stdout="codex ok", stderr="")

    launcher = CodexLauncher(binary_path="/usr/bin/codex", runner=fake_runner)
    result = launcher.launch(
        {
            "task_id": "task_2",
            "goal": "Review the scientific evidence and update result_note.md",
            "deliverables": ["result_note.md"],
            "acceptance_criteria": ["result_note.md exists"],
            "context_refs": {"repo_path": str(tmp_path)},
        }
    )

    assert result["worker_id"] == "codex"
    assert result["status"] == "success"
    assert result["deliverable_paths"] == ["result_note.md"]


def test_worker_result_schema_accepts_valid_payload() -> None:
    result = WorkerResult(
        task_id="task_1",
        worker_id="claude_code",
        status="success",
        deliverable_paths=["metrics.json"],
        summary="Completed bounded task",
    )
    assert result.status == "success"


def test_verification_report_schema_accepts_valid_payload() -> None:
    report = VerificationReport(
        task_id="task_1",
        status="accept",
        failures=[],
        failed_check_types=[],
        rework_priority="none",
        warnings=[],
        recommended_brain_action="CONTINUE",
    )
    assert report.status == "accept"


def test_claude_code_launcher_returns_failed_result_on_timeout(tmp_path: Path) -> None:
    def timeout_runner(command, *, cwd, capture_output, text, timeout, check):  # noqa: ANN001
        raise subprocess.TimeoutExpired(command, timeout)

    launcher = ClaudeCodeLauncher(binary_path="/usr/bin/ccb", runner=timeout_runner, timeout_sec=1)
    result = launcher.launch(
        {
            "task_id": "task_timeout",
            "goal": "Do something",
            "deliverables": ["metrics.json"],
            "acceptance_criteria": [],
            "context_refs": {"repo_path": str(tmp_path)},
        }
    )
    assert result["status"] == "failed"
    assert "timed out" in result["summary"].lower()
