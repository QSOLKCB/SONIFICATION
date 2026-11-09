"""Source-pinned finite checks for the frozen MAT-SPEC-008 run-owner gate."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from formal.sonification.mat008.audit.verify import HERE as AUDIT_HERE
from formal.sonification.mat008.audit.verify import accepted_audit
from formal.sonification.mat008.conformance import (
    MODULE_SHA256,
    PATH,
    REUSE_REASON,
    compile_frozen_slice,
    two_campaign_fixture,
    verify,
)
from formal.sonification.mat008.verify_receipt import verify as verify_receipt

ROOT = Path(__file__).resolve().parents[1]
SOURCE_BINDING_SHA256 = "0745c4178e6c06e8e16f0028eddf2152c480088daa3c35b36d96b5053d7bd0d4"


class Mat008RunOwnershipConformance(unittest.TestCase):
    def checked_checkout_source(self) -> bytes:
        raw = (ROOT / PATH).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), MODULE_SHA256)
        return raw

    def test_checkout_bytes_match_pinned_historical_context(self) -> None:
        """Byte identity works in a shallow checkout; Git tag identity is checked separately."""
        manifest_raw = (ROOT / "formal/sonification/mat008/SOURCE_BINDING.json").read_bytes()
        self.assertEqual(hashlib.sha256(manifest_raw).hexdigest(), SOURCE_BINDING_SHA256)
        manifest = json.loads(manifest_raw)
        self.assertEqual(len(manifest["context_file_identities"]), 14)
        for item in manifest["context_file_identities"]:
            raw = (ROOT / item["path"]).read_bytes()
            self.assertEqual(len(raw), item["bytes"], item["path"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"], item["path"])
        self.checked_checkout_source()

    def test_committed_finite_receipt_is_bound_to_inputs(self) -> None:
        self.assertEqual(verify_receipt()["status"], "FINITE_RECEIPT_BINDING_MATCH")

    def test_exact_builtin_rows_against_pairwise_oracle(self) -> None:
        # The retained conformance receipt separately checked historical Git objects.
        # Here the source bytes are pinned directly so Actions can use a shallow checkout.
        raw = self.checked_checkout_source()
        with patch("formal.sonification.mat008.conformance.frozen_source", return_value=raw):
            receipt = verify(ROOT)
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

        validate, _spans = compile_frozen_slice(self.checked_checkout_source())
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

    def test_retained_independent_audit_file_inventory(self) -> None:
        audit = accepted_audit(AUDIT_HERE / "attempt-001")
        self.assertEqual(audit["proof_input_commit"], "c7889e3c9468ef4354d45d41b467263a0b5dea02")
        self.assertEqual(audit["assurance"]["REFINEMENT_PROVED"], "OPEN")


if __name__ == "__main__":
    unittest.main()
