"""SPARK-002 Phase 1B independent standard-library reference and differential runner.

No physical observations are authenticated, and no GNATprove proof is run here.
SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

SEED = 20261110
MAX_ROWS = 8
CODE_MAX = 65_535
SAMPLE_MAX = 1_000_000


@dataclass(frozen=True)
class Row:
    rid: int
    camp: int
    lab: int
    run: int
    doc: int
    measure: int
    diagnostic: int
    event: int
    registration: int
    role: int
    phase: int
    source: int
    reading: int
    value: int
    error: int
    diag_error: int
    conditions: int

    def as_text(self) -> str:
        return " ".join(str(getattr(self, key)) for key in self.__dataclass_fields__)


def valid_rows(campaigns: int = 2) -> list[Row]:
    """Synthetic declared metadata; never original experimental measurements."""
    assert campaigns in (2, 3, 4)
    rows: list[Row] = []
    for index in range(campaigns):
        c = 100 + 20 * index
        role = index % 2
        for phase in (0, 1):
            rows.append(
                Row(
                    rid=1 + len(rows),
                    camp=c,
                    lab=c + 1,
                    run=c + 2,
                    doc=c + 3,
                    measure=c + 4,
                    diagnostic=c + 5,
                    event=c + 6,
                    registration=900,
                    role=role,
                    phase=phase,
                    source=0,
                    reading=0 if phase == 0 else 1,
                    value=5 if phase == 0 else 0,
                    error=1,
                    diag_error=1,
                    conditions=1,
                )
            )
    return rows


def reading_oracle(ak: int, av: int, bk: int, bv: int) -> str:
    if any(kind not in range(4) for kind in (ak, bk)):
        return "INVALID"
    if any(value < -SAMPLE_MAX or value > SAMPLE_MAX for value in (av, bv)):
        return "INVALID"
    if ak == 3 or bk == 3 or (ak == 1 and av != 0) or (bk == 1 and bv != 0):
        return "INVALID_INPUT"
    if ak == 2 or bk == 2:
        return "MISSING_INPUT"
    if av < bv:
        return "BELOW"
    if av > bv:
        return "ABOVE"
    return "EQUAL"


def _domain(row: Row) -> bool:
    coded = (
        row.rid, row.camp, row.lab, row.run, row.doc,
        row.measure, row.diagnostic, row.event, row.registration,
        row.error, row.diag_error,
    )
    return (
        all(0 <= x <= CODE_MAX for x in coded)
        and -SAMPLE_MAX <= row.value <= SAMPLE_MAX
        and row.role in (0, 1)
        and row.phase in (0, 1, 2)
        and row.source in (0, 1, 2, 3)
        and row.reading in (0, 1, 2, 3)
        and row.conditions in (0, 1)
    )


def packet_oracle(rows: list[Row], *, tampered_tail: bool = False) -> str:
    """Reference uses group ownership maps, not Ada's pair quantifiers."""
    if len(rows) > MAX_ROWS or not all(_domain(row) for row in rows):
        return "INVALID"
    if tampered_tail and len(rows) == MAX_ROWS:
        return "INVALID"  # no unused slot exists to corrupt
    if len(rows) < 4 or tampered_tail:
        return "BLOCKED"

    seen_ids: set[int] = set()
    campaign_context: dict[int, tuple[int, int, int, int, int]] = {}
    owner_maps: dict[str, dict[int, int]] = {
        key: {} for key in ("run", "doc", "measure", "diagnostic", "event")
    }
    labs: dict[int, set[int]] = {0: set(), 1: set()}
    phases: dict[int, set[int]] = {0: set(), 1: set()}
    receipts: set[int] = set()
    for row in rows:
        required = (
            row.rid, row.camp, row.lab, row.run, row.doc,
            row.measure, row.diagnostic, row.event, row.registration,
            row.error, row.diag_error,
        )
        if not all(required):
            return "BLOCKED"
        if row.rid in seen_ids:
            return "BLOCKED"
        seen_ids.add(row.rid)
        if row.measure == row.diagnostic:
            return "BLOCKED"
        if (row.source != 0 or row.phase not in (0, 1)
                or row.reading not in (0, 1)
                or (row.reading == 1 and row.value != 0)
                or row.conditions != 1):
            return "BLOCKED"
        context = (row.role, row.lab, row.run, row.doc, row.measure)
        existing = campaign_context.setdefault(row.camp, context)
        if existing != context:
            return "BLOCKED"
        receipts.add(row.registration)
        labs[row.role].add(row.lab)
        phases[row.role].add(row.phase)
        for field, owners in owner_maps.items():
            code = getattr(row, field)
            if code in owners and owners[code] != row.camp:
                return "BLOCKED"
            owners[code] = row.camp
    if len(receipts) != 1 or labs[0] & labs[1]:
        return "BLOCKED"
    if phases[0] != {0, 1} or phases[1] != {0, 1}:
        return "BLOCKED"
    # A measurement hash may not masquerade as another campaign's diagnostic.
    for code in owner_maps["measure"].keys() & owner_maps["diagnostic"].keys():
        if owner_maps["measure"][code] != owner_maps["diagnostic"][code]:
            return "BLOCKED"
    return "STRUCTURAL_ONLY_UNAUTHENTICATED"


def packet_command(rows: list[Row], *, tampered_tail: bool = False) -> str:
    command = "T" if tampered_tail else "A"
    return " ".join((command, str(len(rows)), *(r.as_text() for r in rows)))


def vectors() -> list[tuple[str, str]]:
    rng = random.Random(SEED)
    cases: list[tuple[str, str]] = []
    sample_values = (-SAMPLE_MAX, -7, 0, 7, SAMPLE_MAX)
    for ak in range(4):
        for bk in range(4):
            for av in sample_values:
                for bv in sample_values:
                    cases.append((f"O {ak} {av} {bk} {bv}",
                                  reading_oracle(ak, av, bk, bv)))
    for command, expected in (
        ("O 4 0 0 0", "INVALID"),
        ("O 0 1000001 0 0", "INVALID"),
        ("O 0 0 0 -1000001", "INVALID"),
        ("A 9", "INVALID"),
        ("A 0", "BLOCKED"),
        ("A 0 99", "INVALID"),
        ("X", "INVALID"),
        ("", "INVALID"),
    ):
        cases.append((command, expected))
    for campaigns in (2, 3, 4):
        rows = valid_rows(campaigns)
        cases.append((packet_command(rows), "STRUCTURAL_ONLY_UNAUTHENTICATED"))
        cases.append((packet_command(rows, tampered_tail=True),
                      "INVALID" if len(rows) == MAX_ROWS else "BLOCKED"))

    base = valid_rows()
    # One-field edits exercise absence, incorrect declarations and collisions.
    changes = (
        ("rid", 0), ("rid", base[0].rid), ("camp", 0),
        ("lab", 0), ("run", 0), ("doc", 0), ("measure", 0),
        ("diagnostic", 0), ("event", 0), ("registration", 0),
        ("source", 1), ("source", 2), ("source", 3),
        ("phase", 2), ("reading", 2), ("reading", 3),
        ("error", 0), ("diag_error", 0), ("conditions", 0),
        ("value", 1), ("measure", base[2].diagnostic),
    )
    for index in (1, 2, 3):
        for field, value in changes:
            altered = base.copy()
            altered[index] = replace(altered[index], **{field: value})
            outcome = packet_oracle(altered)
            cases.append((packet_command(altered), outcome))

    # Across campaigns: mutate the WHOLE declared family to evade the
    # single-campaign inconsistency check, then test independent ownership.
    for field in ("lab", "run", "doc", "measure", "diagnostic", "event"):
        altered = base.copy()
        for index in (2, 3):
            altered[index] = replace(altered[index], **{field: getattr(base[0], field)})
        cases.append((packet_command(altered), packet_oracle(altered)))
    for _ in range(650):
        rows = valid_rows(rng.choice((2, 3, 4)))
        pos = rng.randrange(len(rows))
        field = rng.choice(list(Row.__dataclass_fields__))
        if field == "value":
            value = rng.choice((-SAMPLE_MAX, -1, 0, 1, SAMPLE_MAX, SAMPLE_MAX + 1))
        elif field in ("role", "phase", "source", "reading"):
            value = rng.randrange(5)
        elif field == "conditions":
            value = rng.randrange(3)
        else:
            value = rng.choice((0, 1, rng.randrange(100, 210), CODE_MAX + 1))
        rows[pos] = replace(rows[pos], **{field: value})
        cases.append((packet_command(rows), packet_oracle(rows)))
    return cases


def verify(executable: Path) -> dict[str, object]:
    probe = executable.resolve(strict=True)
    if not probe.is_file() or not probe.stat().st_mode & 0o111:
        raise ValueError("probe must be an executable regular file")
    cases = vectors()
    process = subprocess.run(
        [str(probe)], input="\n".join(request for request, _ in cases) + "\n",
        text=True, capture_output=True, check=False, timeout=60,
        encoding="utf-8", shell=False,
    )
    if process.returncode != 0:
        raise RuntimeError(f"Ada driver failed: {process.returncode}: {process.stderr}")
    outputs = process.stdout.splitlines()
    if len(outputs) != len(cases):
        raise AssertionError(f"output count mismatch: {len(outputs)} != {len(cases)}")
    for number, ((request, expected), actual) in enumerate(
        zip(cases, outputs, strict=True), 1
    ):
        if expected != actual.strip():
            raise AssertionError(
                f"vector {number}: {request!r}, expected {expected!r}, "
                f"observed {actual!r}"
            )
    return {
        "profile": "SPARK-002", "milestone": "phase-1b",
        "status": "EXECUTED_ADA_PYTHON_DIFFERENTIAL_PASS",
        "vectors": len(cases), "seed": SEED,
        "gnatprove": "NOT_INVOKED_BY_DIFFERENTIAL_TEST",
        "physical_evidence_admitted": False,
        "classifier_score_calculated": False,
        "external_identity_authenticated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    print(json.dumps(verify(parser.parse_args().exe), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
