"""Negative checks for pinned SPARK-002 Phase 1B proof evidence.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.verify_spark_002_phase_1b_receipts import SOURCES, verify

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "publication/spark-002/phase-1b"
GIT_SCOPE = "scripts.verify_spark_002_phase_1b_receipts._historical_sources"


class Phase1BProofReceipts(unittest.TestCase):
    def _verify_without_historical_git(self, evidence: Path) -> dict[str, object]:
        # Unit-test receipt parsing locally; production CI checks actual Git history.
        with mock.patch(GIT_SCOPE, return_value=None):
            return verify(ROOT, evidence)

    def _copy_evidence(self, temp: str) -> Path:
        destination = Path(temp) / "evidence"
        shutil.copytree(EVIDENCE, destination)
        return destination

    def test_original_receipts_match_exact_pinned_digests(self) -> None:
        result = self._verify_without_historical_git(EVIDENCE)
        self.assertEqual(result["original_receipts_verified"], 7)
        self.assertEqual(result["historical_sources_verified"], 3)
        self.assertEqual(result["reported_proof_checks"], 9)
        self.assertIs(result["new_prover_run"], False)
        self.assertIs(result["physical_evidence_admitted"], False)

    def test_modified_proof_log_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            evidence = self._copy_evidence(temp)
            path = evidence / "receipts/PROOF.log"
            path.write_bytes(path.read_bytes() + b"unverified modification\n")
            with self.assertRaisesRegex(ValueError, "original receipt SHA-256 mismatch"):
                self._verify_without_historical_git(evidence)

    def test_modified_original_manifest_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            evidence = self._copy_evidence(temp)
            path = evidence / "receipts/SHA256SUMS"
            path.write_bytes(path.read_bytes() + b"x\n")
            with self.assertRaisesRegex(ValueError, "original receipt SHA-256 mismatch"):
                self._verify_without_historical_git(evidence)

    def test_modified_source_receipt_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            evidence = self._copy_evidence(temp)
            path = evidence / "receipts/SOURCES.sha256"
            path.write_bytes(path.read_bytes().replace(b"7242919b", b"6242919b"))
            with self.assertRaisesRegex(ValueError, "original receipt SHA-256 mismatch"):
                self._verify_without_historical_git(evidence)

    def test_derived_audit_cannot_upgrade_physical_claims(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            evidence = self._copy_evidence(temp)
            path = evidence / "AUDIT.json"
            audit = json.loads(path.read_text(encoding="utf-8"))
            audit["admission_boundary"]["physical_evidence_authenticated"] = True
            path.write_text(json.dumps(audit), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "derived audit metadata mismatch"):
                self._verify_without_historical_git(evidence)

    def test_unexpected_original_receipt_member_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            evidence = self._copy_evidence(temp)
            (evidence / "receipts/UNEXPECTED.txt").write_text("extra", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "receipt membership mismatch"):
                self._verify_without_historical_git(evidence)

    def test_linked_original_receipt_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            evidence = self._copy_evidence(temp)
            path = evidence / "receipts/PROOF.log"
            source = evidence / "proof-source"
            path.replace(source)
            path.symlink_to(source)
            with self.assertRaisesRegex(ValueError, "linked original receipt"):
                self._verify_without_historical_git(evidence)

    def test_historical_git_source_hash_mismatch_rejected(self) -> None:
        completed = subprocess.CompletedProcess([], 0, b"different source", b"")
        with mock.patch(
            "scripts.verify_spark_002_phase_1b_receipts.subprocess.run",
            return_value=completed,
        ) as mocked:
            with self.assertRaisesRegex(ValueError, "pinned historical Git source mismatch"):
                verify(ROOT, EVIDENCE)
        self.assertEqual(mocked.call_count, 1)
        self.assertIn("show", mocked.call_args.args[0])

    def test_expected_historical_git_source_paths(self) -> None:
        self.assertEqual(len(SOURCES), 3)
        self.assertTrue(all(path.startswith("verification/spark002/phase1b/")
                            for path in SOURCES))


if __name__ == "__main__":
    unittest.main()
