"""Build MAT-SPEC-009 prospective split and synthetic denial audit.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from materials.mat_spec_009 import build_evidence, write_evidence  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dist/mat-spec-009")
    parser.add_argument("--format", choices=("symbolic",), default="symbolic")
    parser.add_argument("--render-audio", action="store_true", help="always denied")
    args = parser.parse_args()
    if args.render_audio:
        print(json.dumps({"error": "sampled audio is prohibited"}), file=sys.stderr)
        return 2
    try:
        output = build_evidence(ROOT)
        target = write_evidence(ROOT, args.out, output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({
        "destination": str(target), "files": sorted(output),
        "audio_generated": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
