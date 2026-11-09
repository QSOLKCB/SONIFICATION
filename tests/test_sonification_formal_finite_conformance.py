"""Replay the finite MAT-SPEC-007 investigation in the existing Python CI matrix."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "formal/sonification"


def run(*argv: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, *argv], cwd=ROOT, text=True, capture_output=True,
        check=False, timeout=90,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed


def test_frozen_classifier_matches_independent_rational_oracle_on_finite_corpus() -> None:
    completed = run(str(FORMAL / "refinement/run.py"), "--root", str(ROOT))
    report = json.loads(completed.stdout)
    assert report["status"] == "PASS"
    assert report["finite_domain"]["observed_case_count"] == 50630
    assert report["mismatches"] == []
    assert report["implementation_refinement"] == "OPEN"


def test_interval_corpus_and_adversarial_controls() -> None:
    completed = run(
        "-m", "unittest", "discover", "-s", str(FORMAL / "refinement"),
        "-p", "test_*.py", "-v",
    )
    assert "Ran 26 tests" in completed.stderr
    assert "OK" in completed.stderr


def test_retained_independent_audit_binding() -> None:
    completed = run(str(FORMAL / "audit/verify.py"))
    report = json.loads(completed.stdout)
    assert report["status"] == "AUDIT_BINDING_MATCH"
    assert report["refinement"] == "OPEN"
