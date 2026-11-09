#!/usr/bin/env python3
"""Append a command's original streams and local execution metadata."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not args.id.replace("-", "").replace("_", "").isalnum():
        parser.error("safe unique id and command required")
    destination = ROOT / "formal/sonification/evidence" / args.id
    destination.mkdir(exist_ok=False)
    inputs = {}
    for name in args.input:
        path = ROOT / name
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError("input must be an ordinary repository file")
        inputs[name] = digest(path)
    executable = shutil.which(command[0])
    if executable is None:
        raise FileNotFoundError(command[0])
    status = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT)
    diff = subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=ROOT)
    (destination / "worktree-status.txt").write_bytes(status)
    (destination / "tracked-diff.patch").write_bytes(diff)
    started = datetime.now(UTC).isoformat()
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
    (destination / "stdout.log").write_bytes(completed.stdout)
    (destination / "stderr.log").write_bytes(completed.stderr)
    receipt = {
        "schema": "qsol.sonification-formal-001.execution/v1",
        "argv": command, "cwd": str(ROOT), "started_utc": started,
        "ended_utc": datetime.now(UTC).isoformat(), "exit_code": completed.returncode,
        "checkout_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "worktree_status": "DIRTY" if status else "CLEAN",
        "inputs": inputs, "environment": platform.platform(),
        "python": sys.version, "python_executable_sha256": digest(Path(sys.executable)),
        "command_executable": str(Path(executable).resolve()),
        "command_executable_sha256": digest(Path(executable)),
        "stdout_sha256": digest(destination / "stdout.log"),
        "stderr_sha256": digest(destination / "stderr.log"),
        "limits": ["Locally observed execution; no author or external execution attestation",
                   "Input list is explicit; dependency closure requires separate review",
                   "A zero exit status does not establish theorem or coverage acceptance"],
    }
    (destination / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    sys.stdout.buffer.write(completed.stdout)
    sys.stderr.buffer.write(completed.stderr)
    print(json.dumps({"receipt": str(destination.relative_to(ROOT)),
                      "exit_code": completed.returncode}))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
