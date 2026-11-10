#!/usr/bin/env python3
"""Isolated source and receipt deletion controls with preserved raw streams."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AUDIT = Path(__file__).resolve().parent
OUT = AUDIT / "verification-probe-002"
PROOF = ROOT / "formal/sonification/mat009/lean"
EVIDENCE = ROOT / "formal/sonification/evidence"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def run(label: str, argv: list[str], expected_text: str) -> dict:
    result = subprocess.run(
        argv,
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": str(OUT)},
        capture_output=True,
        timeout=180,
    )
    (OUT / f"{label}.stdout").write_bytes(result.stdout)
    (OUT / f"{label}.stderr").write_bytes(result.stderr)
    observed = result.stdout + result.stderr
    return {
        "label": label,
        "argv": argv,
        "cwd": str(ROOT),
        "exit_code": result.returncode,
        "stdout_sha256": sha(result.stdout),
        "stderr_sha256": sha(result.stderr),
        "expected_rejection": result.returncode != 0 and expected_text.encode() in observed,
        "expected_diagnostic": expected_text,
    }


def main() -> int:
    OUT.mkdir(exist_ok=False)
    source = OUT / "source-drift"
    (source / "materials").mkdir(parents=True)
    for name in ("mat_spec_009.py", "mat_spec_008.py"):
        shutil.copyfile(ROOT / "materials" / name, source / "materials" / name)
    target = source / "materials/mat_spec_009.py"
    original = target.read_bytes()
    mutant = original.replace(
        b"CAMPAIGN_CROSSES_TRAIN_HOLDOUT",
        b"CAMPAIGN_CROSSES_TRAIN_HOLDOUT_MUTANT",
        1,
    )
    if mutant == original:
        raise AssertionError("source mutation anchor missing")
    target.write_bytes(mutant)

    finite_receipts = OUT / "source-receipts"
    finite_receipts.mkdir()
    for name in (
        "mat009-source-bind-001",
        "mat009-finite-001",
        "mat009-ruff-source-001",
        "mat009-pytest-001",
    ):
        shutil.copytree(EVIDENCE / name, finite_receipts / name)
    (finite_receipts / "mat009-finite-001/stderr.log").unlink()

    lean_receipt = OUT / "lean-attempt"
    shutil.copytree(PROOF / "attempts/002", lean_receipt)
    (lean_receipt / "build-03-ExactTypes.stdout").unlink()

    negative_archive = OUT / "negative-archive"
    shutil.copytree(PROOF / "negative", negative_archive)
    (negative_archive / "003/weaken_final_leakage_theorem/mutant-source.lean.txt").unlink()

    py = sys.executable
    negative_work = AUDIT / "negative-probe-001/auxiliary_named_false_axiom/work"
    results = [
        run(
            "mutated-source",
            [py, "-B", str(AUDIT / "source_drift_driver.py"), str(source)],
            "working-tree target differs",
        ),
        run(
            "missing-finite-stream",
            [
                py,
                "-B",
                str(ROOT / "formal/sonification/mat009/verify_evidence.py"),
                "--evidence",
                str(finite_receipts),
            ],
            "receipt file inventory changed",
        ),
        run(
            "missing-lean-stream",
            [py, "-B", str(PROOF / "verify.py"), "--attempt", str(lean_receipt)],
            "evidence file inventory changed",
        ),
        run(
            "missing-negative-mutant",
            [py, "-B", str(PROOF / "verify_negative.py"), "--archive", str(negative_archive)],
            "archive file inventory changed",
        ),
        run(
            "mutated-proof-checker",
            [
                py,
                "-B",
                str(AUDIT / "checker_mutant_driver.py"),
                str(negative_work),
                str(OUT / "checker-result"),
            ],
            "stale proof input: SplitModel.lean",
        ),
    ]
    report = {
        "status": "PASS" if all(row["expected_rejection"] for row in results) else "FAIL",
        "source_mutant_sha256": sha(mutant),
        "results": results,
    }
    (OUT / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "detected": sum(row["expected_rejection"] for row in results),
                "total": len(results),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
