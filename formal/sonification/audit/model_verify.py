#!/usr/bin/env python3
"""Check retained independent audit binding; no semantic claim promotion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    attempt = HERE / "attempt-004-model"
    report = json.loads((attempt / "AUDIT.json").read_text())
    if report["status"] != "PASS" or not report["inputs_stable_during_audit"]:
        raise ValueError("audit incomplete")
    for name, expected in report["proof_input_sha256"].items():
        if digest(HERE.parent / "lean" / name) != expected:
            raise ValueError(f"stale audited input: {name}")
        if digest(attempt / "inputs" / (name + ".source")) != expected:
            raise ValueError(f"altered audited input snapshot: {name}")
    if digest(HERE / "model_run.py") != report["audit_runner_sha256"]:
        raise ValueError("stale audit runner")
    if len(report["theorems"]) != 19 or any(
        row["AUDIT_ACCEPTED"] != "PASS" or row["REFINEMENT_PROVED"] != "OPEN"
        for row in report["theorems"]
    ):
        raise ValueError("unexpected theorem/assurance inventory")
    negatives = [c for c in report["checks"] if not c["expected_zero"]]
    if len(negatives) != 8 or any(not c["detected_as_expected"] for c in report["checks"]):
        raise ValueError("incomplete negative controls")
    for directory in attempt.rglob("execution.json"):
        command = json.loads(directory.read_text())
        for stream in ("stdout", "stderr"):
            if digest(directory.parent / (stream + ".log")) != command[stream + "_sha256"]:
                raise ValueError(f"altered command stream: {directory}")
    print(json.dumps({"status": "MODEL_AUDIT_BINDING_MATCH", "theorems": 19,
                      "refinement": "OPEN", "scope": "recorded mathematical statements"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
