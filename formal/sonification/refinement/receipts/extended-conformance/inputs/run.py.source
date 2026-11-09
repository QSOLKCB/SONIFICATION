#!/usr/bin/env python3
"""Run finite conformance against one frozen production operation.

Stdlib only. This command does not certify unbounded source refinement.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import platform
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

from source_adapter import (
    compile_production,
    describe,
    evaluate,
    extract,
    load_frozen,
    oracle,
    outcome,
)


def run(root: Path) -> dict:
    raw = load_frozen(root)
    node = extract(raw)
    production = compile_production(node)
    values = sorted({Fraction(n, d) for n in range(-3, 4) for d in range(1, 4)})
    corpus = hashlib.sha256()
    counts: Counter[str] = Counter()
    mismatches = []
    total = 0
    for endpoints in itertools.product(values, repeat=4):
        a, b = endpoints[:2], endpoints[2:]
        expected = outcome(oracle, a, b)
        observed = outcome(production, a, b)
        interpreted = outcome(lambda x, y: evaluate(node, x, y), a, b)
        identity = [[v.numerator, v.denominator] for v in endpoints]
        record = [identity, expected, observed, interpreted]
        corpus.update((json.dumps(record, separators=(",", ":")) + "\n").encode())
        counts[expected[1] if expected[0] == "return" else expected[0]] += 1
        total += 1
        if expected != observed or expected != interpreted:
            mismatches.append(record)
    # Huge positive denominators and adjacent integers exceed floating precision.
    # Every endpoint is still exact: no float or Decimal conversion occurs.
    huge = 2**4096
    stress = [
        ((Fraction(huge), Fraction(huge)), (Fraction(huge + 1), Fraction(huge + 1))),
        ((Fraction(-huge - 1), Fraction(-huge - 1)), (Fraction(-huge), Fraction(-huge))),
        ((Fraction(1, huge), Fraction(2, huge)), (Fraction(2, huge), Fraction(3, huge))),
        ((Fraction(2, huge), Fraction(1, huge)), (Fraction(0), Fraction(1))),
        ((Fraction(-1, huge), Fraction(1, huge)), (Fraction(0), Fraction(0))),
    ]
    for a, b in stress:
        expected, observed = outcome(oracle, a, b), outcome(production, a, b)
        interpreted = outcome(lambda x, y: evaluate(node, x, y), a, b)
        identity = [[v.numerator, v.denominator] for v in (*a, *b)]
        record = [identity, expected, observed, interpreted]
        corpus.update((json.dumps(record, separators=(",", ":")) + "\n").encode())
        total += 1
        counts[expected[1] if expected[0] == "return" else expected[0]] += 1
        if expected != observed or expected != interpreted:
            mismatches.append(record)
    if total != 50630:
        raise AssertionError("finite case inventory changed")
    return {
        "status": "PASS" if not mismatches else "FAIL",
        "class": "FINITE_CONFORMANCE",
        "implementation_refinement": "OPEN",
        "python": sys.version,
        "implementation": platform.python_implementation(),
        "source": describe(node, raw),
        "finite_domain": {
            "enumeration": (
                "all ordered endpoint quadruples from distinct Fraction(n,d), -3<=n<=3, 1<=d<=3"
            ),
            "unique_endpoint_count": len(values),
            "cartesian_case_count": 50625,
            "additional_4096_bit_cases": len(stress),
            "expected_case_count": 50630,
            "observed_case_count": total,
            "ordering": (
                "ascending exact rational endpoint value; lexicographic Cartesian product; "
                "then documented stress order"
            ),
            "comparison": "exact return strings or exact exception class and message",
        },
        "outcomes": dict(sorted(counts.items())),
        "corpus_sha256": corpus.hexdigest(),
        "mismatches": mismatches,
        "limits": [
            "Finite evidence only; no universal refinement theorem",
            "Source AST and Python runtime remain trusted",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.root)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
