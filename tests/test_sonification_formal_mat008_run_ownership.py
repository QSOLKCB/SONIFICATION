"""Source-pinned finite checks for the frozen MAT-SPEC-008 run-owner gate."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from formal.sonification.mat008.conformance import (
    REUSE_REASON,
    compile_frozen_slice,
    frozen_source,
    two_campaign_fixture,
    verify,
)
from formal.sonification.mat008.verify_receipt import verify as verify_receipt


class Mat008RunOwnershipConformance(unittest.TestCase):
    def test_committed_finite_receipt_is_bound_to_inputs(self) -> None:
        self.assertEqual(verify_receipt()["status"], "FINITE_RECEIPT_BINDING_MATCH")

    def test_exact_builtin_rows_against_pairwise_oracle(self) -> None:
        root = Path(__file__).resolve().parents[1]
        receipt = verify(root)
        self.assertEqual(receipt["status"], "FINITE_CONFORMANCE_PASS")
        self.assertEqual(receipt["exhaustive_generated_cases"], 1296)
        self.assertEqual(receipt["REFINEMENT_PROVED"], "OPEN")
        self.assertTrue(receipt["source_mutation_detected"])
        self.assertTrue(receipt["output_mutation_detected"])

    def test_equal_text_str_subclass_with_inconsistent_hash_is_outside_domain(self) -> None:
        class SaltedStr(str):
            def __new__(cls, value: str, salt: int) -> SaltedStr:
                result = super().__new__(cls, value)
                result.salt = salt
                return result

            def __hash__(self) -> int:
                return super().__hash__() + self.salt

        root = Path(__file__).resolve().parents[1]
        validate, _spans = compile_frozen_slice(frozen_source(root))
        records = two_campaign_fixture()
        for i, item in enumerate(records):
            item["original_run_id"] = SaltedStr("SHARED_RUN", 0 if i < 2 else 1)
        left, right = records[0]["original_run_id"], records[2]["original_run_id"]
        self.assertEqual(left, right)
        self.assertNotEqual(hash(left), hash(right))
        broad_result = validate(records)
        self.assertEqual(broad_result["status"], "STRUCTURAL_ONLY_UNAUTHENTICATED")
        self.assertNotIn(REUSE_REASON, broad_result["reasons"])
        decoded = json.loads(json.dumps(records))
        self.assertIs(type(decoded[0]["original_run_id"]), str)
        self.assertIn(REUSE_REASON, validate(decoded)["reasons"])


if __name__ == "__main__":
    unittest.main()
