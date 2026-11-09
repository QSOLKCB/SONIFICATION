#!/usr/bin/env python3
"""Check retained independent audit binding; no semantic claim promotion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT_SHA256 = "6611453b22b6042f7afdcad5d03de533982913cb0a159a96345a0c4838404848"
SNAPSHOT_SOURCE_COMMIT = "fcce6b0d6287a443282013e04b8e7211e1b36eb2"
SNAPSHOT_TREE = "74f5bda39afc9662a51c9211c7ce878b976406ad"


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


def verify_retained_snapshot(attempt: Path) -> None:
    """Require the exact 198 historical audit files pinned from merged PR #42."""
    manifest_path = HERE / "attempt-003.snapshot.json"
    if attempt.is_symlink() or manifest_path.is_symlink():
        raise ValueError("linked retained audit root or manifest")
    if digest(manifest_path) != SNAPSHOT_SHA256:
        raise ValueError("retained audit snapshot manifest changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest["files"]
    if (
        manifest["source_commit"] != SNAPSHOT_SOURCE_COMMIT
        or manifest["source_tree"] != SNAPSHOT_TREE
        or manifest["attempt"] != "attempt-003"
        or manifest["expected_file_count"] != 198
        or len(expected) != 198
    ):
        raise ValueError("unexpected retained audit snapshot identity")
    observed = set()
    for path in attempt.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"linked retained audit path: {path}")
        if path.is_file():
            observed.add(path.relative_to(attempt).as_posix())
        elif not path.is_dir():
            raise ValueError(f"unsupported retained audit path: {path}")
    if observed != set(expected):
        raise ValueError("retained audit file inventory mismatch")
    for relative, expected_hash in expected.items():
        if digest(attempt / relative) != expected_hash:
            raise ValueError(f"altered retained audit file: {relative}")


def verify_checker_evidence(attempt: Path, report: dict) -> None:
    """Relate the pinned checker results to the accepted theorem statements."""
    nominal = json.loads((attempt / "nominal-build/result.json").read_text())
    declarations = json.loads((attempt / "nominal-build/declarations.json").read_text())
    by_name = {row["declaration"]: row for row in declarations}
    names = {row["declaration"] for row in report["theorems"]}
    if (
        nominal["status"] != report["nominal_proof_result"]
        or nominal["status"] != "PASS"
        or nominal["declaration_count"] != len(declarations)
        or len(by_name) != len(declarations)
        or len(nominal["expected_theorems"]) != len(names)
        or len(nominal["observed_theorems"]) != len(names)
        or set(nominal["expected_theorems"]) != names
        or set(nominal["observed_theorems"]) != names
    ):
        raise ValueError("nominal theorem inventory disagrees with audit")
    for accepted in report["theorems"]:
        original = by_name.get(accepted["declaration"])
        if original is None or (
            original["type"] != accepted["exact_observed_type"]
            or original["axioms"] != accepted["axioms"]
        ):
            raise ValueError(f"accepted theorem differs from checker: {accepted['declaration']}")

    for relative, expected_status in (
        ("nominal-build", "PASS"),
        *((f"{name}/checker", "FAIL") for name in NEGATIVE_MUTATIONS),
    ):
        directory = attempt / relative
        result = json.loads((directory / "result.json").read_text())
        if result["status"] != expected_status:
            raise ValueError(f"unexpected retained checker status: {relative}")
        for command in result["commands"]:
            for stream in ("stdout", "stderr"):
                if digest(directory / command[f"{stream}_path"]) != command[f"{stream}_sha256"]:
                    raise ValueError(f"altered checker command stream: {relative}/{stream}")


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
    verify_retained_snapshot(attempt)
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
    verify_checker_evidence(attempt, report)
    verify_execution_receipts(attempt, report["checks"])
    print(json.dumps({"status": "AUDIT_BINDING_MATCH", "theorems": 19,
                      "refinement": "OPEN", "scope": "recorded mathematical statements"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
