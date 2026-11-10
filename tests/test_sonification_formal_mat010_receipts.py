"""Fail-closed controls for retained MAT010 source and finite receipts."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from formal.sonification.mat010.verify_evidence import RECEIPTS, verify


class Mat010ReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mat010-receipt-control-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("source-001", "finite-001"):
            shutil.copytree(RECEIPTS / name, self.root / name)

    def test_intact_receipts(self) -> None:
        result = verify(self.root)
        self.assertEqual(result["status"], "MAT010_SOURCE_FINITE_RECEIPTS_BOUND")
        self.assertEqual(result["REFINEMENT_PROVED"], "OPEN")

    def test_missing_finite_stream(self) -> None:
        (self.root / "finite-001/stdout.log").unlink()
        with self.assertRaisesRegex(ValueError, "receipt file inventory changed"):
            verify(self.root)

    def test_altered_source_receipt(self) -> None:
        path = self.root / "source-001/receipt.json"
        path.write_text(path.read_text().replace('"exit_code": 0', '"exit_code": 1'))
        with self.assertRaisesRegex(ValueError, "altered receipt file"):
            verify(self.root)


if __name__ == "__main__":
    unittest.main()
