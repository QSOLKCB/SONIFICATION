#!/usr/bin/env python3
"""Exercise the complete checker against an isolated mutated proof module."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

check = importlib.import_module("formal.sonification.mat009.lean.check")


def main() -> int:
    work = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    argv = [
        "check.py",
        "--lean",
        "/home/trent/.elan/toolchains/leanprover--lean4---v4.19.0/bin/lean",
        "--baseline-commit",
        "a09aab6572fb9c3875d5f2940bdb17ec55c358d5",
        "--out",
        str(out),
    ]
    with patch.object(check, "HERE", work), patch.object(sys, "argv", argv):
        return check.main()


if __name__ == "__main__":
    sys.exit(main())
