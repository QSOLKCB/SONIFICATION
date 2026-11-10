"""Focused source-binding and accepted-row run-ownership counterexamples."""

from __future__ import annotations

import ast
import itertools
import json
import unittest
from pathlib import Path

from formal.sonification.mat008.conformance import compile_frozen_slice, row
from formal.sonification.mat008.refinement import source_bind

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "materials/mat_spec_008.py"
MANIFEST = ROOT / "formal/sonification/mat008/refinement/SOURCE_BINDING.json"
REUSE = "REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS"


def has_pairwise_conflict(accepted: list[tuple[str, str]]) -> bool:
    """Independent relation on explicitly designated processed rows."""
    return any(
        left_run == right_run and left_campaign != right_campaign
        for (left_campaign, left_run), (right_campaign, right_run)
        in itertools.combinations(accepted, 2)
    )


class Mat008RefinementBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = SOURCE.read_bytes()
        validator, _ = compile_frozen_slice(cls.raw)
        cls.validate = staticmethod(validator)

    def test_exact_frozen_source_and_selected_ast(self) -> None:
        manifest_raw = MANIFEST.read_bytes()
        self.assertEqual(source_bind.sha(manifest_raw), source_bind.MANIFEST_SHA256)
        manifest = json.loads(manifest_raw, object_pairs_hook=source_bind.unique_pairs)
        result = source_bind.analyze(self.raw, manifest)
        self.assertEqual(result["accepted_identity_fields"], 5)
        self.assertEqual(result["gate_iterations"], 2)
        altered = self.raw.replace(b"owner[prior] = camp", b"owner[prior] = prior", 1)
        self.assertNotEqual(altered, self.raw)
        with self.assertRaisesRegex(ValueError, "source SHA-256 mismatch"):
            source_bind.analyze(altered, manifest)
        altered_module = ast.parse(altered.decode("utf-8"))
        validator = source_bind.only_function(
            altered_module, "validate_future_measurement_packet"
        )
        loop = next(node for node in validator.body if isinstance(node, ast.For))
        gate = next(node for node in loop.body if isinstance(node, ast.For))
        self.assertFalse(source_bind.same_ast(gate, source_bind.GATE))

    def test_processed_projection_and_sticky_reason_on_builtin_rows(self) -> None:
        scenarios: list[tuple[str, list[object], list[tuple[str, str]]]] = []

        same = [row(0, "CAMP_A", "RUN"), row(1, "CAMP_A", "RUN")]
        scenarios.append(("same_campaign", same, [("CAMP_A", "RUN")] * 2))

        overwritten = [
            row(0, "CAMP_A", "RUN"), row(1, "CAMP_B", "RUN"),
            row(2, "CAMP_A", "RUN"), row(3, "CAMP_B", "OTHER"),
        ]
        scenarios.append((
            "repeated_overwrite", overwritten,
            [("CAMP_A", "RUN"), ("CAMP_B", "RUN"),
             ("CAMP_A", "RUN"), ("CAMP_B", "OTHER")],
        ))

        repeated_conflict = [
            row(0, "CAMP_A", "RUN"), row(1, "CAMP_B", "RUN"),
            row(2, "CAMP_A", "RUN"), row(3, "CAMP_C", "RUN"),
        ]
        scenarios.append((
            "repeated_overwrite_then_conflict", repeated_conflict,
            [("CAMP_A", "RUN"), ("CAMP_B", "RUN"),
             ("CAMP_A", "RUN"), ("CAMP_C", "RUN")],
        ))

        skipped = [row(0, "CAMP_A", "RUN"), row(1, "CAMP_B", "RUN")]
        skipped[1]["lab_family_id"] = "invalid-lab"
        scenarios.append(("invalid_identity_skipped", skipped, [("CAMP_A", "RUN")]))

        between = [
            row(0, "CAMP_A", "RUN"), row(1, "CAMP_B", "RUN"),
            row(2, "CAMP_B", "RUN"),
        ]
        between[1]["lab_family_id"] = "invalid-lab"
        scenarios.append((
            "invalid_between_valid_rows", between,
            [("CAMP_A", "RUN"), ("CAMP_B", "RUN")],
        ))

        late_invalid = [row(0, "CAMP_A", "RUN"), row(1, "CAMP_B", "RUN")]
        late_invalid[1]["measurement_value"] = None
        scenarios.append((
            "later_invalid_still_processed", late_invalid,
            [("CAMP_A", "RUN"), ("CAMP_B", "RUN")],
        ))

        duplicate_id = [row(0, "CAMP_A", "RUN"), row(1, "CAMP_B", "RUN")]
        duplicate_id[1]["row_id"] = duplicate_id[0]["row_id"]
        scenarios.append((
            "duplicate_row_id_still_processed", duplicate_id,
            [("CAMP_A", "RUN"), ("CAMP_B", "RUN")],
        ))

        malformed = [row(0, "CAMP_A", "RUN"), None, row(2, "CAMP_B", "RUN")]
        scenarios.append((
            "non_dict_skipped", malformed,
            [("CAMP_A", "RUN"), ("CAMP_B", "RUN")],
        ))

        for name, records, accepted in scenarios:
            with self.subTest(name=name):
                result = self.validate(records)
                self.assertEqual(REUSE in result["reasons"], has_pairwise_conflict(accepted))

        late = [row(0, "CAMP_A", "RUN"), row(1, "CAMP_B", "RUN")]
        self.assertIn(REUSE, self.validate(late)["reasons"])
        self.assertIn(REUSE, self.validate([*late, row(2, "CAMP_B", "OTHER")])["reasons"])

    def test_order_and_subclass_boundaries(self) -> None:
        base = [
            row(0, "CAMP_A", "RUN"), row(1, "CAMP_B", "RUN"),
            row(2, "CAMP_B", "OTHER"),
        ]
        for order in itertools.permutations(base):
            with self.subTest(order=tuple(x["row_id"] for x in order)):
                self.assertIn(REUSE, self.validate(list(order))["reasons"])

        class SaltedStr(str):
            def __new__(cls, value: str, salt: int):
                item = super().__new__(cls, value)
                item.salt = salt
                return item

            def __hash__(self) -> int:
                return super().__hash__() + self.salt

        class NeverDifferent(str):
            def __ne__(self, other: object) -> bool:
                return False

        salted = [row(0, "CAMP_A", "RUN"), row(1, "CAMP_B", "RUN")]
        salted[0]["original_run_id"] = SaltedStr("RUN", 0)
        salted[1]["original_run_id"] = SaltedStr("RUN", 1)
        self.assertNotIn(REUSE, self.validate(salted)["reasons"])
        self.assertIn(REUSE, self.validate(json.loads(json.dumps(salted)))["reasons"])

        unequal = [row(0, "CAMP_A", "RUN"), row(1, "CAMP_B", "RUN")]
        for item in unequal:
            item["campaign_id"] = NeverDifferent(item["campaign_id"])
        self.assertNotIn(REUSE, self.validate(unequal)["reasons"])
        self.assertIn(REUSE, self.validate(json.loads(json.dumps(unequal)))["reasons"])

    def test_ordered_sequences_at_multiple_lengths(self) -> None:
        for length in (1, 2, 3, 4, 17, 64):
            with self.subTest(length=length, kind="distinct_runs"):
                records = [row(i, "CAMP_A", f"RUN_{i}") for i in range(length)]
                self.assertNotIn(REUSE, self.validate(records)["reasons"])
            if length > 1:
                with self.subTest(length=length, kind="late_conflict"):
                    records[-1]["campaign_id"] = "CAMP_B"
                    records[-1]["original_run_id"] = records[0]["original_run_id"]
                    self.assertIn(REUSE, self.validate(records)["reasons"])


if __name__ == "__main__":
    unittest.main()
