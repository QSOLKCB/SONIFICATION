"""Independent finite observations; no claim of source refinement."""

from __future__ import annotations

import ast
import hashlib
import itertools
import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
COMMIT = "b4247877dd471e2e9d4986c86bdc1f11b14e43f8"
SOURCE_SHA256 = "e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08"
REASON = "REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS"


def row(i: int, campaign: str, run: str) -> dict:
    return {
        "campaign_id": campaign,
        "lab_family_id": "LAB_A" if campaign == "CAMP_A" else "LAB_B",
        "original_run_id": run,
        "source_document_id": f"DOC_{i}",
        "row_id": f"ROW_{i}",
        "phase": "HE_I" if i % 2 == 0 else "HE_II",
        "source_type": "ORIGINAL_EXPERIMENTAL_RECORD",
        "synthetic_fixture": False,
        "diagnostic_basis": "INDEPENDENT_NON_TEMPERATURE_DIAGNOSTIC",
        "measurement_value": "1",
        "measurement_sigma": "0.1",
        "diagnostic_sigma": "0.1",
        "source_sha256": chr(ord("a") + i) * 64,
        "pressure_condition": "HE4_SVP",
    }


def main() -> None:
    raw = subprocess.check_output(
        ["git", "show", f"{COMMIT}:materials/mat_spec_008.py"], cwd=ROOT
    )
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA256
    parsed = ast.parse(raw)
    names = {"_identity", "_decimal", "validate_future_measurement_packet"}
    selected = [n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in selected} == names and len(selected) == 3
    assert all(not n.decorator_list for n in selected)
    ns = {"re": re, "Fraction": Fraction}
    exec(compile(ast.Module(selected, []), "frozen-MAT008-audit", "exec"), ns)
    validate = ns["validate_future_measurement_packet"]
    collisions = 0
    cases = 0
    for assignments in itertools.product(
        itertools.product(("CAMP_A", "CAMP_B"), ("RUN_A", "RUN_B", "RUN_C")), repeat=4
    ):
        records = [row(i, campaign, run) for i, (campaign, run) in enumerate(assignments)]
        # An independent grouping/set oracle, unlike the submitted pairwise oracle.
        owners = {}
        for record in records:
            owners.setdefault(record["original_run_id"], set()).add(record["campaign_id"])
        collision = any(len(campaigns) > 1 for campaigns in owners.values())
        result = validate(records)
        assert (REASON in result["reasons"]) == collision
        assert not collision or result["status"] == "BLOCKED"
        assert result["physical_evidence_admitted"] is False
        assert result["independence_authenticated"] is False
        cases += 1
        collisions += int(collision)
    assert cases == 1296 and 0 < collisions < cases

    class SaltedStr(str):
        def __new__(cls, value, salt):
            instance = super().__new__(cls, value)
            instance.salt = salt
            return instance

        def __hash__(self):
            return str.__hash__(self) + self.salt

    records = [row(i, "CAMP_A" if i < 2 else "CAMP_B", "SHARED_RUN") for i in range(4)]
    for pair in (records[:2], records[2:]):
        pair[1]["source_document_id"] = pair[0]["source_document_id"]
        pair[1]["source_sha256"] = pair[0]["source_sha256"]
    for i, record in enumerate(records):
        record["original_run_id"] = SaltedStr("SHARED_RUN", 0 if i < 2 else 1)
    left = records[0]["original_run_id"]
    right = records[2]["original_run_id"]
    assert left == right and hash(left) != hash(right)
    subclass_result = validate(records)
    assert subclass_result["status"] == "STRUCTURAL_ONLY_UNAUTHENTICATED"
    assert REASON not in subclass_result["reasons"]
    decoded = json.loads(json.dumps(records))
    assert all(type(record["original_run_id"]) is str for record in decoded)
    decoded_result = validate(decoded)
    assert decoded_result["status"] == "BLOCKED" and REASON in decoded_result["reasons"]
    print(json.dumps({
        "status": "PASS",
        "scope": "Finite built-in rows, ordinary grouping oracle; not Python refinement",
        "source_commit": COMMIT,
        "module_sha256": SOURCE_SHA256,
        "cases": cases,
        "collision_cases": collisions,
        "noncollision_cases": cases - collisions,
        "str_subclass_equal_values_distinct_hashes": True,
        "str_subclass_status": subclass_result["status"],
        "str_subclass_reuse_reason_present": REASON in subclass_result["reasons"],
        "json_roundtrip_status": decoded_result["status"],
        "json_roundtrip_reuse_reason_present": REASON in decoded_result["reasons"],
        "REFINEMENT_PROVED": "OPEN",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
