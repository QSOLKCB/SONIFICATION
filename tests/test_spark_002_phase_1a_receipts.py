"""Negative tests for historical SPARK-002 receipts. SPDX-License-Identifier: MPL-2.0"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.verify_spark_002_phase_1a_receipts import verify

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "publication/spark-002/phase-1a"

class ReceiptTests(unittest.TestCase):
    def test_historical_receipts_pass(self) -> None:
        result = verify(ROOT, EVIDENCE)
        self.assertEqual(result["original_receipts_verified"], 7)
        self.assertEqual(result["historical_git_sources_verified"], 3)
        self.assertIs(result["new_prover_run"], False)

    def test_modified_log_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "evidence"
            shutil.copytree(EVIDENCE, dest)
            p = dest / "receipts/PROOF.log"
            p.write_bytes(p.read_bytes() + b"tamper\n")
            with self.assertRaisesRegex(ValueError, "original receipt SHA-256 mismatch"):
                verify(ROOT, dest)

    def test_modified_manifest_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "evidence"
            shutil.copytree(EVIDENCE, dest)
            p = dest / "receipts/SHA256SUMS"
            p.write_bytes(p.read_bytes() + b"faked\n")
            with self.assertRaisesRegex(ValueError, "original receipt SHA-256 mismatch"):
                verify(ROOT, dest)

if __name__ == "__main__":
    unittest.main()
