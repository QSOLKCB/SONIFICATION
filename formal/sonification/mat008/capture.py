"""Capture an append-only MAT-SPEC-008 finite-conformance execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    directory = args.out.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    command = [
        sys.executable,
        str(Path(__file__).with_name("conformance.py")),
        "--out",
        str(directory / "result"),
    ]
    run = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        check=False,
        timeout=120,
    )
    (directory / "stdout.log").write_bytes(run.stdout)
    (directory / "stderr.log").write_bytes(run.stderr)
    result = directory / "result" / "receipt.json"
    script = Path(__file__).with_name("conformance.py")
    interpreter = Path(sys.executable).resolve()
    evidence = {
        "argv": command,
        "cwd": str(Path(__file__).resolve().parents[3]),
        "exit_code": run.returncode,
        "input_sha256": {
            "conformance.py": digest(script.read_bytes()),
            "capture.py": digest(Path(__file__).read_bytes()),
        },
        "python_executable": str(interpreter),
        "python_executable_sha256": digest(interpreter.read_bytes()),
        "stdout_sha256": digest(run.stdout),
        "stderr_sha256": digest(run.stderr),
        "receipt_sha256": digest(result.read_bytes()) if result.exists() else None,
        "claim_class": "FINITE_CONFORMANCE_ONLY",
        "REFINEMENT_PROVED": "OPEN",
    }
    (directory / "execution.json").write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"exit_code": run.returncode, "evidence": str(directory)}))
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
