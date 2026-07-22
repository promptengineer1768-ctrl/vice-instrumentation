#!/usr/bin/env python3
"""Launch one isolated instrumented VICE session with owned resources."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Sequence


def reserve_loopback_port(requested: int) -> tuple[socket.socket, int]:
    """Reserve a caller-selected or operating-system-assigned loopback port."""
    reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
    if exclusive is not None:
        reservation.setsockopt(socket.SOL_SOCKET, exclusive, 1)
    reservation.bind(("127.0.0.1", requested))
    return reservation, int(reservation.getsockname()[1])


def atomic_json(path: Path, value: dict[str, object]) -> None:
    """Publish a session record without exposing partially written JSON."""
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def session_command(
    executable: Path, session: Path, port: int, extra: Sequence[str]
) -> list[str]:
    """Build the VICE command with isolated monitor, config, and log paths."""
    return [
        str(executable),
        "-config",
        str(session / "vice.ini"),
        "-logfile",
        str(session / "vice.log"),
        "-binarymonitoraddress",
        f"ip4://127.0.0.1:{port}",
        "-binarymonitor",
        *extra,
    ]


def launch(arguments: argparse.Namespace) -> int:
    """Launch VICE, record ownership, and return its exit status."""
    executable = Path(arguments.vice).resolve()
    if not executable.is_file():
        raise FileNotFoundError(f"VICE executable does not exist: {executable}")
    root = Path(arguments.session_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    session_id = arguments.session_id or uuid.uuid4().hex
    session = root / session_id
    session.mkdir(exist_ok=False)
    reservation, port = reserve_loopback_port(arguments.port)
    command = session_command(executable, session, port, arguments.vice_arguments)
    record: dict[str, object] = {
        "schema": 1,
        "session_id": session_id,
        "session_dir": str(session),
        "monitor_address": f"127.0.0.1:{port}",
        "command": command,
        "launcher_pid": os.getpid(),
        "state": "starting",
    }
    manifest = session / "session.json"
    atomic_json(manifest, record)
    creationflags = 0
    start_new_session = False
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        start_new_session = True
    with (session / "stdout.log").open("wb") as stdout, (
        session / "stderr.log"
    ).open("wb") as stderr:
        reservation.close()
        process = subprocess.Popen(
            command,
            cwd=session,
            stdout=stdout,
            stderr=stderr,
            creationflags=creationflags,
            start_new_session=start_new_session,
        )
        record.update({"child_pid": process.pid, "state": "running"})
        atomic_json(manifest, record)

        def stop_child(_signum: int, _frame: object) -> None:
            if process.poll() is None:
                process.terminate()

        signal.signal(signal.SIGINT, stop_child)
        signal.signal(signal.SIGTERM, stop_child)
        exit_code = process.wait()
    record.update(
        {"state": "exited", "exit_code": exit_code, "finished_unix": time.time()}
    )
    atomic_json(manifest, record)
    if not arguments.keep and exit_code == 0:
        shutil.rmtree(session)
    elif arguments.print_manifest:
        print(manifest)
    return int(exit_code)


def parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--vice", required=True, help="instrumented VICE executable")
    value.add_argument(
        "--session-root",
        default=str(Path(tempfile.gettempdir()) / "vice-instrumented-sessions"),
    )
    value.add_argument("--session-id")
    value.add_argument("--port", type=int, default=0)
    value.add_argument("--keep", action="store_true")
    value.add_argument("--print-manifest", action="store_true")
    value.add_argument("vice_arguments", nargs=argparse.REMAINDER)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    """Run the isolated-session launcher."""
    arguments = parser().parse_args(argv)
    if arguments.vice_arguments[:1] == ["--"]:
        arguments.vice_arguments = arguments.vice_arguments[1:]
    if not 0 <= arguments.port <= 65535:
        parser().error("--port must be between 0 and 65535")
    return launch(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
