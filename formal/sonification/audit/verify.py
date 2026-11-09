#!/usr/bin/env python3
"""Check retained independent audit binding; no semantic claim promotion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


# The frozen independent audit contains one nominal proof, eight mutated
# proofs, one historical source inventory replay, and two Python checks.
# Do not derive the required inventory solely from whatever files remain.
NEGATIVE_MUTATIONS = (
    "false_theorem",
    "weaker_theorem",
    "hidden_data_sorry",
    "custom_axiom",
    "unimported_nested_module",
    "missing_import",
    "empty_zero_exit_report",
    "missing_expected_inventory",
)
EXPECTED_EXECUTION_DIRS = (
    "nominal-command",
    *(f"{name}/command" for name in NEGATIVE_MUTATIONS),
    "source-inventory",
    "finite-conformance",
    "refinement-tests",
)
RECEIPT_FIELDS = frozenset(
    {
        "argv",
        "cwd",
        "exit_code",
        "stdout_sha256",
        "stderr_sha256",
        "expected_zero",
        "detected_as_expected",
    }
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_execution_receipts(attempt: Path, checks: list[dict]) -> None:
    """Require all 12 frozen receipts and bind each stream to AUDIT.json."""
    if len(checks) != len(EXPECTED_EXECUTION_DIRS):
        raise ValueError("execution receipt count mismatch")

    expected_paths = {
        f"{directory}/execution.json" for directory in EXPECTED_EXECUTION_DIRS
    }
    observed_paths = {
        path.relative_to(attempt).as_posix()
        for path in attempt.rglob("execution.json")
    }
    if observed_paths != expected_paths:
        raise ValueError("execution receipt inventory mismatch")

    for location, audit_check in zip(EXPECTED_EXECUTION_DIRS, checks, strict=True):
        mutation = location.split("/", 1)[0] if location.endswith("/command") else None
        expected_keys = RECEIPT_FIELDS | ({"mutation"} if mutation else set())
        if set(audit_check) != expected_keys or (
            mutation is not None and audit_check["mutation"] != mutation
        ):
            raise ValueError(f"unexpected audit check identity: {location}")

        directory = attempt / location
        receipt_path = directory / "execution.json"
        if directory.is_symlink() or receipt_path.is_symlink() or not receipt_path.is_file():
            raise ValueError(f"missing or linked execution receipt: {location}")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if set(receipt) != RECEIPT_FIELDS:
            raise ValueError(f"unexpected execution receipt fields: {location}")
        if any(receipt[key] != audit_check[key] for key in RECEIPT_FIELDS):
            raise ValueError(f"execution receipt disagrees with AUDIT.json: {location}")
        if not receipt["detected_as_expected"] or (
            (receipt["exit_code"] == 0) != receipt["expected_zero"]
        ):
            raise ValueError(f"incorrect execution outcome: {location}")

        for stream in ("stdout", "stderr"):
            stream_path = directory / f"{stream}.log"
            if stream_path.is_symlink() or not stream_path.is_file():
                raise ValueError(f"missing or linked command stream: {location}/{stream}")
            if digest(stream_path) != audit_check[f"{stream}_sha256"]:
                raise ValueError(f"altered command stream: {location}/{stream}")


def main() -> int:
    attempt = HERE / "attempt-003"
    report = json.loads((attempt / "AUDIT.json").read_text())
    if report["status"] != "PASS" or not report["inputs_stable_during_audit"]:
        raise ValueError("audit incomplete")
    for name, expected in report["proof_input_sha256"].items():
        if digest(HERE.parent / "lean" / name) != expected:
            raise ValueError(f"stale audited input: {name}")
        if digest(attempt / "inputs" / (name + ".source")) != expected:
            raise ValueError(f"altered audited input snapshot: {name}")
    if digest(HERE / "run.py") != report["audit_runner_sha256"]:
        raise ValueError("stale audit runner")
    if len(report["theorems"]) != 19 or any(
        row["AUDIT_ACCEPTED"] != "PASS" or row["REFINEMENT_PROVED"] != "OPEN"
        for row in report["theorems"]
    ):
        raise ValueError("unexpected theorem/assurance inventory")
    negatives = [c for c in report["checks"] if not c["expected_zero"]]
    if len(negatives) != 8 or any(not c["detected_as_expected"] for c in report["checks"]):
        raise ValueError("incomplete negative controls")
    verify_execution_receipts(attempt, report["checks"])
    print(json.dumps({"status": "AUDIT_BINDING_MATCH", "theorems": 19,
                      "refinement": "OPEN", "scope": "recorded mathematical statements"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
