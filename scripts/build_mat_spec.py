"""Build MAT-SPEC-001 symbolic artifacts offline using only the standard library.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from materials.mat_spec import build_bundle, write_bundle  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dist/mat-spec-001")
    parser.add_argument(
        "--source", type=Path, help="byte-identical copy of the pinned source table"
    )
    parser.add_argument("--format", choices=("symbolic",), default="symbolic")
    parser.add_argument("--render-audio", action="store_true", help="always rejected")
    args = parser.parse_args()
    try:
        artifacts = build_bundle(ROOT, args.source, render_audio=args.render_audio)
        output = write_bundle(ROOT, args.out, artifacts)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(
        json.dumps(
            {"output": str(output), "files": sorted(artifacts), "audio_generated": False},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
