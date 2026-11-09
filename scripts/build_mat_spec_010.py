"""Build MAT-SPEC-010 final numbered research evidence and archive index.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from materials.mat_spec_010 import build_evidence, write_evidence  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dist/mat-spec-010")
    parser.add_argument("--format", choices=("symbolic",), default="symbolic")
    parser.add_argument("--render-audio", action="store_true", help="always denied")
    args = parser.parse_args()
    if args.render_audio:
        print(json.dumps({"error": "root rendered audio prohibited"}), file=sys.stderr)
        return 2
    try:
        products = build_evidence(ROOT)
        target = write_evidence(ROOT, args.out, products)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({
        "destination": str(target), "files": sorted(products),
        "audio_generated": False, "archive_deposited": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
