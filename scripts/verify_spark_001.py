#!/usr/bin/env python3
"""Deterministic Ada/Python differential oracle for SPARK-001. MPL-2.0.

Finite software evidence only; not a formal proof or physical result.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
from pathlib import Path

SEED = 20261109
MIN_CENTS = -999_999
MAX_CENTS = 999_999
DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]{0,3})\.[0-9]{2}\Z", re.ASCII)


def parse_oracle(source: str) -> str:
    if not DECIMAL.fullmatch(source):
        return "INVALID"
    raw = source.lstrip("-")
    whole, fraction = raw.split(".")
    cents = int(whole) * 100 + int(fraction)
    if source.startswith("-"):
        cents = -cents
    return f"OK {cents}"


def interval_oracle(lk: int, ll: int, lh: int, rk: int, rl: int, rh: int) -> str:
    if ll > lh or rl > rh or (
        lk == 2 and (ll != 0 or lh != 0)
    ) or (rk == 2 and (rl != 0 or rh != 0)):
        return "INVALID"
    if lk not in (1, 2) or rk not in (1, 2):
        return "MISSING"
    if lh < rl:
        return "BELOW"
    if rh < ll:
        return "ABOVE"
    return "OVERLAP"


def vectors() -> list[tuple[str, str]]:
    rng = random.Random(SEED)
    result: list[tuple[str, str]] = []
    decimals = [
        "0.00", "-0.00", "1.00", "-1.00", "9999.99", "-9999.99",
        "1.01", "-1234.56", "99.99", "0001.00", "01.00", "+1.00",
        "1.0", "1.000", "NaN", "Infinity", "1e2", "", "-.01",
        "12.3a", "10000.00", "99999.99",
    ]
    for _ in range(130):
        n = rng.randrange(0, 1_000_000)
        decimal = f"{n // 100}.{n % 100:02d}"
        decimals.append(("-" if rng.randrange(2) else "") + decimal)
    result.extend((f"P {s}", parse_oracle(s)) for s in decimals)
    samples = [
        (1, 0, 3, 1, 3, 10),
        (1, 0, 2, 1, 3, 4),
        (1, 3, 4, 1, 0, 2),
        (0, 0, 0, 2, 0, 0),
        (2, 0, 0, 1, 0, 0),
        (3, 0, 0, 1, 0, 0),
        (2, 1, 1, 1, 0, 0),
        (1, 2, 1, 1, 0, 1),
        (1, MIN_CENTS, MAX_CENTS, 1, MIN_CENTS, MAX_CENTS),
    ]
    for sample in samples:
        result.append(("I " + " ".join(map(str, sample)), interval_oracle(*sample)))
    for _ in range(200):
        lk, rk = rng.randrange(4), rng.randrange(4)
        pairs = []
        for kind in (lk, rk):
            if kind == 2:
                pairs.extend((0, 0))
            else:
                a = rng.randint(MIN_CENTS, MAX_CENTS)
                b = rng.randint(MIN_CENTS, MAX_CENTS)
                pairs.extend(sorted((a, b)))
        sample = (lk, pairs[0], pairs[1], rk, pairs[2], pairs[3])
        result.append(("I " + " ".join(map(str, sample)), interval_oracle(*sample)))
    result.extend((f"L {n}", "TRUE" if n == 1 else "FALSE") for n in range(1, 12))
    return result


def validated_executable(executable: Path) -> Path:
    try:
        resolved = executable.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"probe executable does not exist: {executable}") from error
    if not resolved.is_file():
        raise ValueError(f"probe executable is not a regular file: {resolved}")
    if not os.access(resolved, os.X_OK):
        raise ValueError(f"probe executable is not executable: {resolved}")
    return resolved


def verify(executable: Path) -> dict:
    cases = vectors()
    probe = validated_executable(executable)
    # The caller intentionally selects this validated probe. A one-element argv
    # with shell parsing disabled prevents shell metacharacters from being evaluated.
    response = subprocess.run(  # nosemgrep
        [str(probe)],
        input="\n".join(x for x, _ in cases) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8",
        timeout=45,
        check=False,
        shell=False,
    )
    if response.returncode:
        raise RuntimeError(f"native probe exit {response.returncode}: {response.stderr}")
    actual = response.stdout.splitlines()
    if len(actual) != len(cases):
        raise AssertionError(f"result count {len(actual)} != {len(cases)}")
    for n, ((request, expected), observed) in enumerate(
        zip(cases, actual, strict=True), 1
    ):
        if observed.strip() != expected:
            raise AssertionError(
                f"SPARK-001 differential {n}: {request!r}, "
                f"expected {expected!r}, got {observed!r}"
            )
    return {
        "profile": "SPARK-001",
        "status": "EXECUTED_ADA_PYTHON_DIFFERENTIAL_PASS",
        "vectors": len(cases),
        "seed": SEED,
        "proof_tool": "NOT_INVOKED_BY_DIFFERENTIAL_TEST",
        "physical_validation": False,
        "audio_generated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    receipt = verify(parser.parse_args().exe)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
