#!/usr/bin/env python3
"""Small independent CPython observations for the frozen MAT009/MAT008 pair."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

mat_spec_009 = importlib.import_module("materials.mat_spec_009")

OUT = Path(__file__).resolve().parent / "independent-cpython-001.json"
TARGET_SHA = "a68089df7d1901fb7c17ffc2889b844b3573024aec4b66348f9c2ef71930c690"
PARENT_SHA = "e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08"


def fixture() -> list[dict]:
    rows = []
    for index, (campaign, lab, role, source, diagnostic) in enumerate(
        (
            ("CAMP_A", "LAB_A", "TRAIN", "a" * 64, "c" * 64),
            ("CAMP_B", "LAB_B", "HOLDOUT", "b" * 64, "d" * 64),
        )
    ):
        for phase in ("HE_I", "HE_II"):
            rows.append(
                {
                    "row_id": f"ROW_{index}_{phase}",
                    "campaign_id": campaign,
                    "lab_family_id": lab,
                    "original_run_id": f"RUN_{index}",
                    "source_document_id": f"DOC_{index}",
                    "source_sha256": source,
                    "diagnostic_sha256": diagnostic,
                    "diagnostic_event_id": f"DIAG_{index}_{phase}",
                    "source_type": "ORIGINAL_EXPERIMENTAL_RECORD",
                    "measurement_quantity": "HEAT_CAPACITY",
                    "measurement_unit": "J_PER_MOL_K",
                    "measurement_value": "12.34",
                    "measurement_sigma": "0.01",
                    "diagnostic_sigma": "0.02",
                    "diagnostic_basis": "INDEPENDENT_NON_TEMPERATURE_DIAGNOSTIC",
                    "label_basis": "ORTHOGONAL_DIAGNOSTIC",
                    "phase": phase,
                    "receiver_scale": "5",
                    "pre_registration_sha256": "e" * 64,
                    "pressure_condition": "HE4_SVP",
                    "study_role": role,
                }
            )
    return rows


class HashString(str):
    def __new__(cls, value: str, assigned_hash: int):
        result = str.__new__(cls, value)
        result.assigned_hash = assigned_hash
        return result

    def __hash__(self) -> int:
        return self.assigned_hash


class UnhashableString(str):
    __hash__ = None


class ExplodingDict(dict):
    def get(self, key, default=None):
        raise RuntimeError("dict subclass get failed")


def no_physical_claim(result: dict) -> bool:
    return (
        result["physical_evidence_admitted"] is False
        and result["independence_authenticated"] is False
        and result["heldout_accuracy"] is None
    )


def main() -> int:
    observed_sha = {
        name: hashlib.sha256((ROOT / "materials" / name).read_bytes()).hexdigest()
        for name in ("mat_spec_009.py", "mat_spec_008.py")
    }
    assert observed_sha == {"mat_spec_009.py": TARGET_SHA, "mat_spec_008.py": PARENT_SHA}

    clean = mat_spec_009.check_future_challenge(fixture())
    assert clean["status"] == "STRUCTURAL_ONLY_UNAUTHENTICATED" and clean["reasons"] == []
    assert no_physical_claim(clean)

    invalid_role_rows = fixture()
    invalid_role_rows[0].update(
        {
            "study_role": "UNDECLARED",
            "measurement_unit": "BAD",
            "receiver_scale": "BAD",
            "diagnostic_sha256": None,
            "pre_registration_sha256": "",
        }
    )
    invalid_role = mat_spec_009.check_future_challenge(invalid_role_rows)
    assert invalid_role["reasons"] == [
        "TRAIN_REQUIRES_BOTH_PHASES",
        "UNDECLARED_TRAIN_HOLDOUT_ROLE",
    ]
    assert no_physical_claim(invalid_role)

    parent_skip_rows = fixture()
    parent_skip_rows[0]["original_run_id"] = ""
    parent_skip = mat_spec_009.check_future_challenge(parent_skip_rows)
    assert parent_skip["reasons"] == [
        "BOTH_PHASES_REQUIRED_FOR_EACH_CAMPAIGN",
        "MISSING_OR_INVALID_SOURCE_IDENTITIES",
    ]
    assert parent_skip["train_campaigns"] == 1 and no_physical_claim(parent_skip)

    first = HashString("SAME_CAMP", 11)
    second = HashString("SAME_CAMP", 23)
    assert first == second and hash(first) != hash(second)
    subclass_rows = fixture()
    for row in subclass_rows[:2]:
        row["campaign_id"] = first
    for row in subclass_rows[2:]:
        row["campaign_id"] = second
    subclass_result = mat_spec_009.check_future_challenge(subclass_rows)
    assert subclass_result["reasons"] == [] and no_physical_claim(subclass_result)
    for row in subclass_rows:
        row["campaign_id"] = "SAME_CAMP"
    builtin_result = mat_spec_009.check_future_challenge(subclass_rows)
    assert {"CAMPAIGN_CROSSES_TRAIN_HOLDOUT", "SOURCE_FAMILY_LEAKAGE_ACROSS_SPLITS"} <= set(
        builtin_result["reasons"]
    )
    assert no_physical_claim(builtin_result)

    exploding_rows = fixture()
    exploding_rows[0] = ExplodingDict(exploding_rows[0])
    try:
        mat_spec_009.check_future_challenge(exploding_rows)
    except RuntimeError as error:
        assert str(error) == "dict subclass get failed"
        exploding = type(error).__name__
    else:
        raise AssertionError("dict subclass did not raise")
    unhashable_rows = fixture()
    unhashable_rows[0]["row_id"] = UnhashableString("ROW_0_HE_I")
    try:
        mat_spec_009.check_future_challenge(unhashable_rows)
    except TypeError as error:
        unhashable = type(error).__name__
    else:
        raise AssertionError("unhashable row identity did not raise")

    marked_rows = fixture()
    for row in marked_rows:
        row["synthetic_fixture"] = True
    marked = mat_spec_009.check_future_challenge(marked_rows)
    assert marked["reasons"] == ["SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT"]
    for row in marked_rows:
        row["synthetic_fixture"] = 1
    integer_marker = mat_spec_009.check_future_challenge(marked_rows)
    assert integer_marker["reasons"] == [] and no_physical_claim(integer_marker)

    controls = mat_spec_009.negative_controls()
    assert len(controls) == 14 and all(
        row["result"] == "PASS_REJECTED" and row["physical_evidence_admitted"] == "false"
        for row in controls
    )
    report = {
        "status": "PASS_FOR_LISTED_CASES_ONLY",
        "source_sha256": observed_sha,
        "clean_status": clean["status"],
        "clean_reasons": clean["reasons"],
        "invalid_role_reasons": invalid_role["reasons"],
        "parent_skip_reasons": parent_skip["reasons"],
        "subclass_equal_text_unequal_hash_reasons": subclass_result["reasons"],
        "builtin_same_text_reason_count": len(builtin_result["reasons"]),
        "dict_subclass_exception": exploding,
        "unhashable_string_exception": unhashable,
        "synthetic_true_reasons": marked["reasons"],
        "synthetic_integer_one_reasons": integer_marker["reasons"],
        "synthetic_control_count": len(controls),
        "physical_evidence_admitted": False,
        "cpython_refinement": "OPEN",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
