#!/usr/bin/env python3
"""Independent bounded SPARK-002 Ada/Python differential oracle (MPL-2.0).

Finite evidence only. Does not invoke GNATprove or admit physics.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
from pathlib import Path

SEED = 20261110
CENTER_MIN, CENTER_MAX = -4_000_000, 4_000_000
ERROR_MAX = 1_000_000
SOURCE_KINDS = 7


def interval_oracle(a: int, ea: int, b: int, eb: int) -> str:
    if not (CENTER_MIN <= a <= CENTER_MAX and CENTER_MIN <= b <= CENTER_MAX):
        return "INVALID"
    if not (0 <= ea <= ERROR_MAX and 0 <= eb <= ERROR_MAX):
        return "INVALID"
    if a + ea < b - eb:
        return "A_BELOW_B"
    if b + eb < a - ea:
        return "B_BELOW_A"
    return "OVERLAP"


def scale_oracle(a: int, ea: int, b: int, eb: int, factor: int) -> str:
    if interval_oracle(a, ea, b, eb) == "INVALID" or not 1 <= factor <= 8:
        return "INVALID"
    left = ((a - ea) * factor, (a + ea) * factor)
    right = ((b - eb) * factor, (b + eb) * factor)
    if left[1] < right[0]:
        scaled = "A_BELOW_B"
    elif right[1] < left[0]:
        scaled = "B_BELOW_A"
    else:
        scaled = "OVERLAP"
    return str(interval_oracle(a, ea, b, eb) == scaled).upper()


def gate_oracle(kind: int, mask: int, camps: int, pairs: int,
                error_rows: int, diagnostic_rows: int) -> str:
    if not (0 <= kind < SOURCE_KINDS and 0 <= mask <= 31
            and 0 <= camps <= 4 and 0 <= pairs <= 6
            and 0 <= error_rows <= 65_535
            and 0 <= diagnostic_rows <= 65_535):
        return "INVALID"
    if (kind == 0 and mask == 31 and camps >= 2 and pairs >= 1
            and error_rows > 0 and diagnostic_rows > 0):
        return "STRUCTURAL_ONLY_UNAUTHENTICATED"
    return "BLOCKED"


def provenance_oracle(mode: int) -> str:
    if not 1 <= mode <= 11:
        return "INVALID"
    return "TRUE" if mode == 1 else "FALSE"


def vectors() -> list[tuple[str, str]]:
    rng = random.Random(SEED)
    data: list[tuple[str, str]] = []
    intervals = [
        (0, 0, 0, 0),       # touching / exact zero
        (0, 1, 2, 1),       # boundary touch
        (-5, 0, 5, 0),      # strictly below
        (5, 0, -5, 0),      # strictly above
        (-4_000_000, 1_000_000, 4_000_000, 1_000_000),
        (4_000_000, 1_000_000, -4_000_000, 1_000_000),
        (4_000_001, 0, 0, 0),   # outside admitted domain
        (0, -1, 0, 0),
        (0, 0, 0, 1_000_001),
    ]
    for _ in range(240):
        intervals.append((rng.randint(CENTER_MIN, CENTER_MAX),
                          rng.randint(0, ERROR_MAX),
                          rng.randint(CENTER_MIN, CENTER_MAX),
                          rng.randint(0, ERROR_MAX)))
    for a, ea, b, eb in intervals:
        data.append((f"I {a} {ea} {b} {eb}", interval_oracle(a, ea, b, eb)))
        for factor in (1, 2, 8):
            data.append((f"S {a} {ea} {b} {eb} {factor}",
                         scale_oracle(a, ea, b, eb, factor)))
    for kind in range(SOURCE_KINDS):
        for mask in (0, 15, 23, 30, 31):
            data.append((f"G {kind} {mask} 2 1 2 2",
                         gate_oracle(kind, mask, 2, 1, 2, 2)))
    for _ in range(220):
        kind = rng.randrange(SOURCE_KINDS)
        mask = rng.randrange(32)
        camps = rng.randrange(5)
        pairs = rng.randrange(7)
        errors = rng.randrange(3)
        diagnostics = rng.randrange(3)
        data.append((f"G {kind} {mask} {camps} {pairs} {errors} {diagnostics}",
                     gate_oracle(kind, mask, camps, pairs, errors, diagnostics)))
    data.extend((f"G {kind} 31 4 6 4 4", gate_oracle(kind, 31, 4, 6, 4, 4))
                for kind in range(SOURCE_KINDS))
    data.extend((f"G 0 31 2 1 {e} {d}", gate_oracle(0, 31, 2, 1, e, d))
                for e, d in ((0, 0), (0, 1), (1, 0), (1, 1)))
    data.append(("G 0 31 1 0 0 0", "BLOCKED"))
    data.extend((f"P {mode}", provenance_oracle(mode)) for mode in range(13))
    data.extend(("F", "BLOCKED_NO_SCORE") for _ in range(2))
    return data


def verify(executable: Path) -> dict[str, object]:
    probe = executable.resolve(strict=True)
    if not probe.is_file():
        raise ValueError("probe is not a regular file")
    if not (probe.stat().st_mode & 0o111):
        raise ValueError("probe is not executable")
    cases = vectors()
    process = subprocess.run(
        [str(probe)], input="\n".join(p for p, _ in cases) + "\n",
        text=True, capture_output=True, check=False, timeout=50,
        encoding="utf-8", shell=False,
    )
    if process.returncode != 0:
        raise RuntimeError(f"Ada probe exit {process.returncode}: {process.stderr}")
    observed = process.stdout.splitlines()
    if len(observed) != len(cases):
        raise AssertionError(f"output count mismatch: {len(observed)} != {len(cases)}")
    for index, ((request, expected), answer) in enumerate(zip(cases, observed, strict=True), 1):
        if answer.strip() != expected:
            raise AssertionError(
                f"case {index}: {request!r}, expected {expected!r}, got {answer!r}"
            )
    return {
        "profile": "SPARK-002", "milestone": "phase-1a",
        "status": "EXECUTED_ADA_PYTHON_DIFFERENTIAL_PASS",
        "vectors": len(cases), "seed": SEED,
        "gnatprove": "NOT_INVOKED_BY_DIFFERENTIAL_TEST",
        "source_authentication": False,
        "physical_evidence_admitted": False,
        "classifier_score_calculated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    print(json.dumps(verify(parser.parse_args().exe), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
