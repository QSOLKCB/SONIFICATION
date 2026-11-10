"""Fail-closed controls for retained MAT009 source and finite receipts."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from formal.sonification.mat009.verify_evidence import EVIDENCE, RECEIPTS, verify


class Mat009ReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mat009-receipt-control-")
        self.addCleanup(self.temp.cleanup)
        self.evidence = Path(self.temp.name)
        for name in RECEIPTS:
            shutil.copytree(EVIDENCE / name, self.evidence / name)

    def test_intact_receipts(self) -> None:
        result = verify(self.evidence)
        self.assertEqual(result["status"], "MAT009_SOURCE_FINITE_RECEIPTS_BOUND")
        self.assertEqual(result["REFINEMENT_PROVED"], "OPEN")

    def test_missing_mandatory_receipt(self) -> None:
        shutil.rmtree(self.evidence / "mat009-finite-001")
        with self.assertRaisesRegex(ValueError, "missing ordinary receipt directory"):
            verify(self.evidence)

    def test_missing_recorded_stream(self) -> None:
        (self.evidence / "mat009-finite-001/stderr.log").unlink()
        with self.assertRaisesRegex(ValueError, "receipt file inventory changed"):
            verify(self.evidence)

    def test_altered_recorded_stream(self) -> None:
        (self.evidence / "mat009-finite-001/stderr.log").write_text("Ran 18 tests; OK\n")
        with self.assertRaisesRegex(ValueError, "recorded stderr changed"):
            verify(self.evidence)

    def test_altered_receipt_claim(self) -> None:
        receipt = self.evidence / "mat009-source-bind-001/receipt.json"
        receipt.write_text(receipt.read_text().replace('"exit_code": 0', '"exit_code": 1'))
        with self.assertRaisesRegex(ValueError, "receipt changed"):
            verify(self.evidence)

    def test_altered_worktree_status(self) -> None:
        (self.evidence / "mat009-pytest-001/worktree-status.txt").write_text("clean\n")
        with self.assertRaisesRegex(ValueError, "recorded worktree status changed"):
            verify(self.evidence)


if __name__ == "__main__":
    unittest.main()
