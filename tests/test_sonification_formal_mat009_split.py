"""Finite, source-pinned checks of the MAT009 split gate.

All rows below are fabricated, self-declared metadata. A structural pass is
never physical admission, source authentication, or an empirical score.
"""

from __future__ import annotations

import hashlib
import unittest
from itertools import combinations, product
from pathlib import Path
from unittest.mock import patch

from materials import mat_spec_008, mat_spec_009

ROOT = Path(__file__).resolve().parents[1]
MAT009_SHA256 = "a68089df7d1901fb7c17ffc2889b844b3573024aec4b66348f9c2ef71930c690"
MAT008_SHA256 = "e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08"


def self_declared_rows(
    campaigns: tuple[tuple[str, str, str], ...] = (
        ("CAMP_A", "LAB_A", "TRAIN"),
        ("CAMP_B", "LAB_B", "HOLDOUT"),
    ),
) -> list[dict]:
    """Make independent fake metadata, without using production fixtures."""
    rows: list[dict] = []
    for index, (campaign, lab, role) in enumerate(campaigns):
        source = "abcd"[index] * 64
        diagnostic = "5678"[index] * 64
        for phase in ("HE_I", "HE_II"):
            rows.append({
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
                "pre_registration_sha256": "f" * 64,
                "pressure_condition": "HE4_SVP",
                "study_role": role,
            })
    return rows


class DivergentHashString(str):
    """Equal text with unequal hashes violates the built-in string contract."""

    def __new__(cls, value: str, assigned_hash: int) -> DivergentHashString:
        instance = str.__new__(cls, value)
        instance.assigned_hash = assigned_hash
        return instance

    def __hash__(self) -> int:
        return self.assigned_hash


class UnhashableString(str):
    __hash__ = None


class ExplodingDict(dict):
    def get(self, key: object, default: object = None) -> object:
        raise RuntimeError("dict subclass get failed")


class SplitGateFiniteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        for path, expected in (
            ("materials/mat_spec_009.py", MAT009_SHA256),
            ("materials/mat_spec_008.py", MAT008_SHA256),
        ):
            observed = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            if observed != expected:
                raise AssertionError(f"frozen source drift: {path}: {observed}")

    def assert_no_physical_claim(self, result: dict) -> None:
        self.assertIs(result["physical_evidence_admitted"], False)
        self.assertIs(result["independence_authenticated"], False)
        self.assertIsNone(result["heldout_accuracy"])

    def test_self_declared_builtins_pass_structure_only(self) -> None:
        rows = self_declared_rows()
        with patch.object(
            mat_spec_008,
            "validate_future_measurement_packet",
            wraps=mat_spec_008.validate_future_measurement_packet,
        ) as parent_call:
            result = mat_spec_009.check_future_challenge(rows)
        self.assertEqual(parent_call.call_count, 1)
        self.assertEqual(result["status"], "STRUCTURAL_ONLY_UNAUTHENTICATED")
        self.assertEqual(result["reasons"], [])
        self.assertEqual((result["train_campaigns"], result["heldout_campaigns"]), (1, 1))
        self.assertIs(result["trained_classifier"], False)
        self.assert_no_physical_claim(result)

    def test_outer_guard_returns_before_parent_with_short_result(self) -> None:
        expected = {
            "status": "BLOCKED",
            "reasons": ["EMPTY_OR_MALFORMED_CHALLENGE"],
            "physical_evidence_admitted": False,
            "independence_authenticated": False,
            "heldout_accuracy": None,
        }
        for bad in (None, (), {}, [], [{}] * 10001):
            length = len(bad) if bad is not None else None
            with (
                self.subTest(kind=type(bad).__name__, length=length),
                patch.object(
                    mat_spec_008,
                    "validate_future_measurement_packet",
                    side_effect=AssertionError("parent must not run"),
                ),
            ):
                self.assertEqual(mat_spec_009.check_future_challenge(bad), expected)

    def test_campaign_cross_split_is_sticky_in_both_row_orders(self) -> None:
        for reversed_order in (False, True):
            rows = self_declared_rows()
            rows[1]["study_role"] = "HOLDOUT"
            if reversed_order:
                rows.reverse()
            result = mat_spec_009.check_future_challenge(rows)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["reasons"], sorted({
                "CAMPAIGN_CROSSES_TRAIN_HOLDOUT",
                "DIAGNOSTIC_PROVENANCE_LEAKAGE_ACROSS_SPLITS",
                "SOURCE_FAMILY_LEAKAGE_ACROSS_SPLITS",
                "TRAIN_REQUIRES_BOTH_PHASES",
            }))
            self.assert_no_physical_claim(result)

    def test_lab_overlap_blocks_distinct_campaigns_without_parent_reason(self) -> None:
        rows = self_declared_rows((
            ("CAMP_A", "LAB_A", "TRAIN"),
            ("CAMP_B", "LAB_B", "TRAIN"),
            ("CAMP_C", "LAB_A", "HOLDOUT"),
        ))
        self.assertEqual(mat_spec_008.validate_future_measurement_packet(rows)["reasons"], [])
        result = mat_spec_009.check_future_challenge(rows)
        self.assertEqual(result["reasons"], ["SOURCE_FAMILY_LEAKAGE_ACROSS_SPLITS"])
        self.assertEqual((result["train_campaigns"], result["heldout_campaigns"]), (2, 1))
        self.assert_no_physical_claim(result)

    def test_small_builtin_split_domain_matches_pairwise_oracle(self) -> None:
        """Compare map/set outcomes with independent row-pair relations."""
        roles = ("TRAIN", "HOLDOUT")
        campaigns = ("CAMP_A", "CAMP_B")
        labs = ("LAB_A", "LAB_B")
        for chosen_roles in product(roles, repeat=4):
            for chosen_campaigns in product(campaigns, repeat=4):
                for chosen_labs in product(labs, repeat=4):
                    rows = self_declared_rows()
                    for index, row in enumerate(rows):
                        row["study_role"] = chosen_roles[index]
                        row["campaign_id"] = chosen_campaigns[index]
                        row["lab_family_id"] = chosen_labs[index]
                    reasons = mat_spec_009.check_future_challenge(rows)["reasons"]
                    pairs = tuple(combinations(range(4), 2))
                    cross_campaign = any(
                        chosen_roles[i] != chosen_roles[j]
                        and chosen_campaigns[i] == chosen_campaigns[j]
                        for i, j in pairs
                    )
                    shared_family = any(
                        chosen_roles[i] != chosen_roles[j]
                        and (
                            chosen_campaigns[i] == chosen_campaigns[j]
                            or chosen_labs[i] == chosen_labs[j]
                        )
                        for i, j in pairs
                    )
                    self.assertEqual(
                        "CAMPAIGN_CROSSES_TRAIN_HOLDOUT" in reasons,
                        cross_campaign,
                    )
                    self.assertEqual(
                        "SOURCE_FAMILY_LEAKAGE_ACROSS_SPLITS" in reasons,
                        shared_family,
                    )
                    self.assertEqual(reasons, sorted(set(reasons)))

    def test_invalid_role_skips_later_child_fields_but_parent_runs(self) -> None:
        rows = self_declared_rows()
        rows[0].update({
            "study_role": "UNDECLARED",
            "measurement_unit": "WRONG",
            "receiver_scale": "10",
            "diagnostic_sha256": None,
            "pre_registration_sha256": "",
        })
        self.assertEqual(mat_spec_008.validate_future_measurement_packet(rows)["reasons"], [])
        result = mat_spec_009.check_future_challenge(rows)
        self.assertEqual(result["reasons"], [
            "TRAIN_REQUIRES_BOTH_PHASES", "UNDECLARED_TRAIN_HOLDOUT_ROLE",
        ])
        self.assert_no_physical_claim(result)

    def test_invalid_family_skips_later_child_fields_and_parent_row(self) -> None:
        rows = self_declared_rows()
        rows[0].update({
            "campaign_id": "",
            "measurement_unit": "WRONG",
            "receiver_scale": "10",
            "diagnostic_sha256": None,
            "pre_registration_sha256": "",
        })
        result = mat_spec_009.check_future_challenge(rows)
        self.assertEqual(result["reasons"], sorted({
            "BOTH_PHASES_REQUIRED_FOR_EACH_CAMPAIGN",
            "MISSING_EXPERIMENT_FAMILY_IDENTITY",
            "MISSING_OR_INVALID_SOURCE_IDENTITIES",
            "TRAIN_REQUIRES_BOTH_PHASES",
        }))
        self.assert_no_physical_claim(result)

    def test_parent_only_identity_skip_still_allows_child_split_row(self) -> None:
        rows = self_declared_rows()
        rows[0]["original_run_id"] = ""
        parent = mat_spec_008.validate_future_measurement_packet(rows)
        self.assertEqual(parent["reasons"], [
            "BOTH_PHASES_REQUIRED_FOR_EACH_CAMPAIGN",
            "MISSING_OR_INVALID_SOURCE_IDENTITIES",
        ])
        result = mat_spec_009.check_future_challenge(rows)
        self.assertEqual(result["reasons"], parent["reasons"])
        self.assertEqual((result["train_campaigns"], result["heldout_campaigns"]), (1, 1))
        self.assertNotIn("TRAIN_REQUIRES_BOTH_PHASES", result["reasons"])
        self.assert_no_physical_claim(result)

    def test_parent_run_document_and_byte_reasons_survive_union(self) -> None:
        cases = (
            ("original_run_id", "REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS"),
            ("source_document_id", "REUSED_ORIGINAL_DOCUMENT_ACROSS_CAMPAIGNS"),
            ("source_sha256", "REUSED_SOURCE_BYTES_ACROSS_CAMPAIGNS"),
        )
        for field, reason in cases:
            with self.subTest(field=field):
                rows = self_declared_rows()
                for row in rows[2:]:
                    row[field] = rows[0][field]
                self.assertEqual(
                    mat_spec_008.validate_future_measurement_packet(rows)["reasons"],
                    [reason],
                )
                result = mat_spec_009.check_future_challenge(rows)
                self.assertEqual(result["reasons"], [reason])
                self.assert_no_physical_claim(result)

    def test_diagnostic_hash_and_event_are_independent_ownership_keys(self) -> None:
        for field in ("diagnostic_sha256", "diagnostic_event_id"):
            with self.subTest(field=field):
                rows = self_declared_rows()
                rows[2][field] = rows[0][field]
                result = mat_spec_009.check_future_challenge(rows)
                self.assertEqual(result["reasons"], [
                    "DIAGNOSTIC_PROVENANCE_LEAKAGE_ACROSS_SPLITS",
                    "DIAGNOSTIC_PROVENANCE_REUSED_ACROSS_CAMPAIGNS",
                ])
                self.assert_no_physical_claim(result)

    def test_same_campaign_diagnostic_document_and_event_reuse_is_allowed(self) -> None:
        rows = self_declared_rows()
        rows[1]["diagnostic_event_id"] = rows[0]["diagnostic_event_id"]
        result = mat_spec_009.check_future_challenge(rows)
        self.assertEqual(result["reasons"], [])
        self.assertEqual(result["status"], "STRUCTURAL_ONLY_UNAUTHENTICATED")
        self.assert_no_physical_claim(result)

    def test_invalid_diagnostic_key_is_not_registered_other_key_still_is(self) -> None:
        for field, bad in (("diagnostic_sha256", None), ("diagnostic_event_id", "bad")):
            with self.subTest(field=field):
                rows = self_declared_rows()
                rows[0][field] = bad
                rows[2][field] = bad
                result = mat_spec_009.check_future_challenge(rows)
                self.assertEqual(result["reasons"], ["INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED"])
        rows = self_declared_rows()
        rows[0]["diagnostic_sha256"] = None
        rows[2]["diagnostic_sha256"] = None
        rows[2]["diagnostic_event_id"] = rows[0]["diagnostic_event_id"]
        result = mat_spec_009.check_future_challenge(rows)
        self.assertEqual(result["reasons"], [
            "DIAGNOSTIC_PROVENANCE_LEAKAGE_ACROSS_SPLITS",
            "DIAGNOSTIC_PROVENANCE_REUSED_ACROSS_CAMPAIGNS",
            "INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED",
        ])
        self.assert_no_physical_claim(result)

    def test_receipt_set_counts_only_valid_unskipped_digests(self) -> None:
        rows = self_declared_rows()
        rows[0]["pre_registration_sha256"] = ""
        self.assertEqual(mat_spec_009.check_future_challenge(rows)["reasons"], [
            "MISSING_PROSPECTIVE_REGISTRATION_RECEIPT",
        ])
        rows = self_declared_rows()
        rows[0]["pre_registration_sha256"] = "0" * 64
        self.assertEqual(mat_spec_009.check_future_challenge(rows)["reasons"], [
            "INCONSISTENT_PREREGISTRATION_RECEIPT",
        ])
        rows = self_declared_rows()
        for row in rows:
            row["pre_registration_sha256"] = ""
        self.assertEqual(mat_spec_009.check_future_challenge(rows)["reasons"], [
            "INCONSISTENT_PREREGISTRATION_RECEIPT",
            "MISSING_PROSPECTIVE_REGISTRATION_RECEIPT",
        ])

    def test_identifier_and_digest_are_ascii_boundaries(self) -> None:
        for accepted in ("A", "_", "0", "A" * 100, DivergentHashString("ABC", 1)):
            self.assertTrue(mat_spec_009._identifier(accepted))
        for rejected in ("", "A" * 101, "a", "É", " A", "A\n", None, 7):
            self.assertFalse(mat_spec_009._identifier(rejected))
        self.assertTrue(mat_spec_009._digest("a" * 64))
        self.assertTrue(mat_spec_009._digest(DivergentHashString("a" * 64, 1)))
        for rejected in ("A" * 64, "a" * 63, "g" * 64, None):
            self.assertFalse(mat_spec_009._digest(rejected))

    def test_equal_text_str_subclass_hashes_can_evade_split_detection(self) -> None:
        first = DivergentHashString("SAME_CAMP", 11)
        second = DivergentHashString("SAME_CAMP", 23)
        self.assertEqual(first, second)
        self.assertNotEqual(hash(first), hash(second))
        rows = self_declared_rows()
        for row in rows[:2]:
            row["campaign_id"] = first
        for row in rows[2:]:
            row["campaign_id"] = second
        observed = mat_spec_009.check_future_challenge(rows)
        self.assertEqual(observed["reasons"], [])
        self.assertEqual(observed["status"], "STRUCTURAL_ONLY_UNAUTHENTICATED")
        self.assert_no_physical_claim(observed)
        for row in rows:
            row["campaign_id"] = "SAME_CAMP"
        builtins_observed = mat_spec_009.check_future_challenge(rows)
        self.assertIn("CAMPAIGN_CROSSES_TRAIN_HOLDOUT", builtins_observed["reasons"])
        self.assertIn("SOURCE_FAMILY_LEAKAGE_ACROSS_SPLITS", builtins_observed["reasons"])
        self.assert_no_physical_claim(builtins_observed)

    def test_subclass_methods_and_unhashable_identifiers_can_raise(self) -> None:
        class ListSubclass(list):
            pass

        class DictSubclass(dict):
            pass

        rows = ListSubclass(DictSubclass(row) for row in self_declared_rows())
        self.assertEqual(
            mat_spec_009.check_future_challenge(rows)["status"],
            "STRUCTURAL_ONLY_UNAUTHENTICATED",
        )
        rows = self_declared_rows()
        rows[0] = ExplodingDict(rows[0])
        with self.assertRaisesRegex(RuntimeError, "dict subclass get failed"):
            mat_spec_009.check_future_challenge(rows)
        rows = self_declared_rows()
        rows[0]["row_id"] = UnhashableString("ROW_0_HE_I")
        with self.assertRaises(TypeError):
            mat_spec_009.check_future_challenge(rows)

    def test_synthetic_flag_uses_identity_and_never_admits_physics(self) -> None:
        rows = self_declared_rows()
        for row in rows:
            row["synthetic_fixture"] = True
        marked = mat_spec_009.check_future_challenge(rows)
        self.assertEqual(marked["reasons"], [
            "SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT",
        ])
        self.assert_no_physical_claim(marked)
        for row in rows:
            row["synthetic_fixture"] = 1
        truthy_integer = mat_spec_009.check_future_challenge(rows)
        self.assertEqual(truthy_integer["reasons"], [])
        self.assertEqual(truthy_integer["status"], "STRUCTURAL_ONLY_UNAUTHENTICATED")
        self.assert_no_physical_claim(truthy_integer)

    def test_fourteen_frozen_negative_controls_are_synthetic_only(self) -> None:
        expected = (
            ("SYNTHETIC_CANDIDATE_DENIED", "SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT"),
            ("CROSS_CAMPAIGN_RUN_REUSE", "REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS"),
            ("CAMPAIGN_SPLIT_LEAKAGE", "CAMPAIGN_CROSSES_TRAIN_HOLDOUT"),
            ("SOURCE_BYTES_REUSED", "REUSED_SOURCE_BYTES_ACROSS_CAMPAIGNS"),
            ("TEMPERATURE_DERIVED_LABEL", "CIRCULAR_OR_MISSING_PHASE_DIAGNOSTIC"),
            ("ZERO_MEASUREMENT_SIGMA", "MISSING_CALIBRATED_MEASUREMENT_UNCERTAINTY"),
            ("ORTHOGONAL_DIAGNOSTIC_ABSENT", "INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED"),
            ("DIAGNOSTIC_SOURCE_EQUALS_MEASUREMENT", "INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED"),
            ("UNDECLARED_RECEIVER_SCALE", "UNDECLARED_RECEIVER_SCALE"),
            ("MISSING_PROSPECTIVE_REGISTRATION", "MISSING_PROSPECTIVE_REGISTRATION_RECEIPT"),
            ("MIXED_PHYSICAL_PRESSURE", "UNDECLARED_PRESSURE_CONDITION"),
            ("HOLDOUT_MISSING_PHASE", "HOLDOUT_REQUIRES_BOTH_PHASES"),
            ("DERIVED_FIT_AS_MEASUREMENT", "DERIVED_FIT_OR_COMPILATION_IS_NOT_PRIMARY_DATA"),
            ("DOCUMENT_REUSED", "REUSED_ORIGINAL_DOCUMENT_ACROSS_CAMPAIGNS"),
        )
        controls = mat_spec_009.negative_controls()
        self.assertEqual(tuple(
            (row["control_id"], row["expected_rejection"]) for row in controls
        ), expected)
        self.assertEqual(tuple(row["control_id"] for row in controls), mat_spec_009.CONTROL_IDS)
        for row in controls:
            self.assertEqual(row["observed_rejection"], row["expected_rejection"])
            self.assertEqual(row["result"], "PASS_REJECTED")
            self.assertEqual(row["synthetic_only"], "true")
            self.assertEqual(row["physical_evidence_admitted"], "false")
            self.assertEqual(row["classifier_accuracy"], "NULL")


if __name__ == "__main__":
    unittest.main()
