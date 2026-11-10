#!/usr/bin/env python3
"""Feed the auxiliary-name mutant's original Lean log to the fixed-count gate."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
check = importlib.import_module("formal.sonification.mat009.lean.check")
AUDIT = Path(__file__).resolve().parent
LEAN = Path("/home/trent/.elan/toolchains/leanprover--lean4---v4.19.0/bin/lean")


def main() -> int:
    raw = (
        AUDIT / "negative-probe-001/auxiliary_named_false_axiom/build-04-LeanAudit.stdout"
    ).read_bytes()
    check.audit_output(raw, LEAN, AUDIT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
