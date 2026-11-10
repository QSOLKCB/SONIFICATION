#!/usr/bin/env python3
"""Recompute retained MAT009 archive digests and inspect original job streams."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AUDIT = Path(__file__).resolve().parent
PROOF = ROOT / "formal/sonification/mat009/lean"
EVIDENCE = ROOT / "formal/sonification/evidence"
OUT = AUDIT / "archive-integrity-001.json"
BASELINE = "a09aab6572fb9c3875d5f2940bdb17ec55c358d5"
SOURCE_CHECKPOINT = "38b5f9e99a5ce3f267c004362acf00ac0dc11342"
LEAN = Path("/home/trent/.elan/toolchains/leanprover--lean4---v4.19.0/bin/lean")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read(path: Path) -> bytes:
    assert path.is_file() and not path.is_symlink(), path
    return path.read_bytes()


def check_manifest(directory: Path, expected_digest: str, filename: str) -> tuple[dict, int]:
    manifest = directory / filename
    raw = read(manifest)
    assert sha(raw) == expected_digest, manifest
    parsed = json.loads(raw)
    files = parsed["files_sha256"]
    observed = {str(path.relative_to(directory)) for path in directory.rglob("*") if path.is_file()}
    assert observed == set(files) | {filename}, directory
    for name, digest in files.items():
        assert sha(read(directory / name)) == digest, name
    return parsed, len(files)


def main() -> int:
    attempt = PROOF / "attempts/002"
    manifest, files = check_manifest(
        attempt,
        "c068cb09fa08737a25bf49c17fa7cbca1e31dbbaa5ab388532b5529e1e41c817",
        "EVIDENCE_MANIFEST.json",
    )
    assert manifest["proof_input_commit"] == BASELINE
    nominal = json.loads(read(attempt / "result.json"))
    assert nominal["status"] == "PASS" and nominal["REFINEMENT_PROVED"] == "OPEN"
    assert sha(read(LEAN)) == nominal["lean_executable_sha256"]
    for filename, digest in nominal["input_sha256"].items():
        relative = f"formal/sonification/mat009/lean/{filename}"
        assert sha(read(ROOT / relative)) == digest
        historical = subprocess.check_output(["git", "show", f"{BASELINE}:{relative}"], cwd=ROOT)
        assert sha(historical) == digest
    for label in (
        "lean-version",
        "build-00-SplitModel",
        "build-01-DiagnosticFirstOwner",
        "build-02-TypedConsumer",
        "build-03-ExactTypes",
        "build-04-LeanAudit",
    ):
        job = json.loads(read(attempt / f"{label}.json"))
        assert job["exit_code"] == 0 and not job["timed_out"]
        for stream in ("stdout", "stderr"):
            assert sha(read(attempt / f"{label}.{stream}")) == job[f"{stream}_sha256"]
    original_audit = read(attempt / "build-04-LeanAudit.stdout")
    independent_audit = read(AUDIT / "independent-replay-001/build-04-LeanAudit.stdout")
    assert original_audit == independent_audit
    imports = json.loads(read(attempt / "toolchain-imports.json"))
    assert len(imports) == 1303
    toolchain = LEAN.parent.parent
    for module, record in imports.items():
        relative = Path("lib/lean") / (module.replace(".", "/") + ".olean")
        assert str(relative) == record["relative_path"]
        assert sha(read(toolchain / relative)) == record["sha256"]

    negative = PROOF / "negative"
    neg_manifest, neg_files = check_manifest(
        negative,
        "6d99b5c41017d87922ffd01f3b34eccab692806ca38b760299371cbcc0d0750b",
        "ARCHIVE_MANIFEST.json",
    )
    assert neg_manifest["nominal_proof_input_commit"] == BASELINE
    prior1 = json.loads(read(negative / "001/result.json"))
    prior2 = json.loads(read(negative / "002/result.json"))
    assert prior1["status"] == "FAILED_DEVELOPMENT_ATTEMPT" and prior1["exit_code"] != 0
    assert prior2["status"] == "FAIL" and sum(x["detected"] for x in prior2["cases"]) == 4
    negative_result = json.loads(read(negative / "003/result.json"))
    assert negative_result["status"] == "PASS" and len(negative_result["cases"]) == 6
    cases = {}
    for item in negative_result["cases"]:
        name = item["mutation"]
        path = negative / "003" / name
        detail = json.loads(read(path / "result.json"))
        assert detail["detected"] and item["detected"]
        assert (
            detail["mutation"] == name
            and detail["observed_failure_module"] == item["observed_failure_module"]
        )
        assert sha(read(path / "mutant-source.lean.txt")) == detail["mutant_sha256"]
        for index, job in enumerate(detail["commands"]):
            module = job["argv"][-1].removesuffix(".lean")
            label = f"build-{index:02d}-{module}"
            for stream in ("stdout", "stderr"):
                assert sha(read(path / f"{label}.{stream}")) == job[f"{stream}_sha256"]
            assert job["exit_code"] == (0 if index + 1 < len(detail["commands"]) else 1)
            assert not job["timed_out"]
        final = detail["commands"][-1]
        label = f"build-{len(detail['commands']) - 1:02d}-{detail['observed_failure_module']}"
        output = read(path / f"{label}.stdout") + read(path / f"{label}.stderr")
        assert detail["expected_diagnostic_text"].encode() in output
        cases[name] = {"module": detail["observed_failure_module"], "exit_code": final["exit_code"]}

    receipt_names = (
        "mat009-source-bind-001",
        "mat009-finite-001",
        "mat009-ruff-source-001",
        "mat009-pytest-001",
    )
    receipts = {}
    for name in receipt_names:
        directory = EVIDENCE / name
        assert {p.name for p in directory.iterdir()} == {
            "receipt.json",
            "stdout.log",
            "stderr.log",
            "worktree-status.txt",
            "tracked-diff.patch",
        }
        receipt = json.loads(read(directory / "receipt.json"))
        assert receipt["checkout_commit"] == SOURCE_CHECKPOINT and receipt["exit_code"] == 0
        assert read(directory / "tracked-diff.patch") == b""
        for stream in ("stdout", "stderr"):
            assert sha(read(directory / f"{stream}.log")) == receipt[f"{stream}_sha256"]
        for relative, digest in receipt["inputs"].items():
            assert sha(read(ROOT / relative)) == digest
            historical = subprocess.check_output(
                ["git", "show", f"{SOURCE_CHECKPOINT}:{relative}"],
                cwd=ROOT,
            )
            assert sha(historical) == digest
        receipts[name] = {
            "receipt_sha256": sha(read(directory / "receipt.json")),
            "exit_code": receipt["exit_code"],
            "input_count": len(receipt["inputs"]),
        }

    full = EVIDENCE / "mat009-full-pytest-001"
    full_receipt = json.loads(read(full / "receipt.json"))
    assert full_receipt["checkout_commit"] == "94a357284408e6bc24cfb9b2d49e9d4144791042"
    assert full_receipt["exit_code"] == 0 and full_receipt["inputs"] == {}
    assert full_receipt["argv"] == ["python3", "-m", "pytest", "-q"]
    assert sha(read(full / "stdout.log")) == full_receipt["stdout_sha256"]
    assert sha(read(full / "stderr.log")) == full_receipt["stderr_sha256"]
    assert b"329 passed, 202 subtests passed" in read(full / "stdout.log")
    report = {
        "status": "PASS",
        "nominal_manifest_sha256": sha(read(attempt / "EVIDENCE_MANIFEST.json")),
        "nominal_file_count": files,
        "nominal_audit_stdout_matches_independent_replay": True,
        "toolchain_import_count": len(imports),
        "negative_manifest_sha256": sha(read(negative / "ARCHIVE_MANIFEST.json")),
        "negative_file_count": neg_files,
        "negative_cases": cases,
        "failed_development_attempts_retained": 2,
        "source_receipts": receipts,
        "full_pytest_receipt_sha256": sha(read(full / "receipt.json")),
        "full_pytest_stdout_sha256": full_receipt["stdout_sha256"],
        "full_pytest_exit_code": full_receipt["exit_code"],
        "full_pytest_reported": "329 passed, 202 subtests passed",
        "full_pytest_inputs_explicitly_listed": len(full_receipt["inputs"]),
        "cpython_refinement": "OPEN",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "nominal_files": files,
                "negative_cases": len(cases),
                "source_receipts": len(receipts),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
