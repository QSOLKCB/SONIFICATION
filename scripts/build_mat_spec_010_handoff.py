"""Build the corrected post-release MAT-SPEC-010 Zenodo deposit.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from materials.mat_spec_010_archive import verify_archive  # noqa: E402
from materials.mat_spec_010_handoff import ARCHIVE_NAME, build_archive  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument("--publication-root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / ARCHIVE_NAME)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.verify_only:
            result = {"verification": verify_archive(args.out.resolve())}
        else:
            result = build_archive(
                repository=args.repository.resolve(),
                publication_root=args.publication_root.resolve(),
                output=args.out.resolve(),
                python=args.python,
            )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
