"""Build MAT-SPEC-005 two-sided helium reference controls, symbolic only.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from materials.mat_spec_005 import build_evidence, write_evidence  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dist/mat-spec-005")
    parser.add_argument("--format", choices=("symbolic",), default="symbolic")
    parser.add_argument("--render-audio", action="store_true", help="always rejected")
    args = parser.parse_args()
    if args.render_audio:
        print(json.dumps({"error": "sampled audio is disabled"}), file=sys.stderr)
        return 2
    try:
        artifacts = build_evidence(ROOT)
        path = write_evidence(ROOT, args.out, artifacts)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({
        "output": str(path), "files": sorted(artifacts), "audio_generated": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
