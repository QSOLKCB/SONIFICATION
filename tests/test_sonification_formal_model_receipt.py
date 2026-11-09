"""Fail CI when the retained SONIFICATION model proof or audit input goes stale."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "formal/sonification/audit/model_verify.py"


def test_retained_model_proof_audit_binding() -> None:
    completed = subprocess.run(
        [sys.executable, str(VERIFIER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert '"status": "MODEL_AUDIT_BINDING_MATCH"' in completed.stdout
