#!/usr/bin/env python3
"""Run the unmodified binder against an isolated mutated working source."""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

source_bind = importlib.import_module("formal.sonification.mat009.source.source_bind")


def frozen_git(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(ROOT), *arguments],
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def main() -> int:
    isolated = Path(sys.argv[1]).resolve()
    with patch.object(source_bind, "ROOT", isolated), patch.object(source_bind, "git", frozen_git):
        source_bind.verify()
    return 0


if __name__ == "__main__":
    sys.exit(main())
