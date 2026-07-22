"""Concurrency and ownership contracts for the VICE session launcher."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vice_session", ROOT / "tools" / "vice_session.py"
)
assert SPEC is not None and SPEC.loader is not None
VICE_SESSION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VICE_SESSION)


def test_dynamic_monitor_ports_are_unique() -> None:
    """Concurrent reservations never publish one shared monitor port."""
    first, first_port = VICE_SESSION.reserve_loopback_port(0)
    second, second_port = VICE_SESSION.reserve_loopback_port(0)
    try:
        assert first_port != second_port
    finally:
        first.close()
        second.close()


def test_command_isolates_monitor_config_and_log(tmp_path: Path) -> None:
    """Every session command points state and monitoring at its own paths."""
    command = VICE_SESSION.session_command(
        tmp_path / "x64sc.exe", tmp_path / "session-a", 43123, ["-warp"]
    )
    assert command[-1] == "-warp"
    assert Path(command[command.index("-config") + 1]).name == "vice.ini"
    assert Path(command[command.index("-logfile") + 1]).name == "vice.log"
    assert command[command.index("-binarymonitoraddress") + 1] == (
        "ip4://127.0.0.1:43123"
    )


def test_launcher_records_only_its_child_and_retains_evidence(tmp_path: Path) -> None:
    """The manifest names the owned child and its isolated artifacts."""
    if os.name == "nt":
        child = tmp_path / "fake_vice.cmd"
        child.write_text("@exit /b 0\n", encoding="utf-8")
    else:
        child = tmp_path / "fake_vice"
        child.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        child.chmod(0o755)
    arguments = argparse.Namespace(
        vice=str(child),
        session_root=str(tmp_path / "sessions"),
        session_id="owned",
        port=0,
        keep=True,
        print_manifest=False,
        vice_arguments=[],
    )
    VICE_SESSION.session_command = lambda *_args: [str(child)]
    assert VICE_SESSION.launch(arguments) == 0
    manifest = json.loads(
        (tmp_path / "sessions" / "owned" / "session.json").read_text("utf-8")
    )
    assert manifest["state"] == "exited"
    assert manifest["exit_code"] == 0
    assert manifest["child_pid"] != manifest["launcher_pid"]
    assert (tmp_path / "sessions" / "owned" / "stdout.log").is_file()
