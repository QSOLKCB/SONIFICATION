"""Fail-closed controls for retained MAT010 source and proof receipts."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from formal.sonification.mat010.verify_evidence import (
    HERE,
    RECEIPTS,
    verify,
    verify_development,
)


class Mat010ReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mat010-receipt-control-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("source-001", "finite-001", "finite-dev-001",
                     "proof-001", "negative-001",
                     "proof-002", "negative-002"):
            shutil.copytree(RECEIPTS / name, self.root / name)

    def test_intact_receipts(self) -> None:
        result = verify(self.root)
        self.assertEqual(result["status"], "MAT010_ALL_RETAINED_RECEIPTS_BOUND")
        self.assertEqual(result["REFINEMENT_PROVED"], "OPEN")
        self.assertEqual(result["receipt_count"], 6)

    def test_missing_finite_stream(self) -> None:
        (self.root / "finite-001/stdout.log").unlink()
        with self.assertRaisesRegex(ValueError, "receipt file inventory changed"):
            verify(self.root)

    def test_altered_source_receipt(self) -> None:
        path = self.root / "source-001/receipt.json"
        path.write_text(path.read_text().replace('"exit_code": 0', '"exit_code": 1'))
        with self.assertRaisesRegex(ValueError, "altered receipt file"):
            verify(self.root)

    def test_missing_proof_stdout(self) -> None:
        (self.root / "proof-002/build-02-LeanAudit.stdout").unlink()
        with self.assertRaisesRegex(ValueError, "receipt file inventory changed"):
            verify(self.root)

    def test_altered_negative_mutant(self) -> None:
        path = self.root / "negative-002/compiler_suffix_false_axiom_cstage2"
        (path / "mutant-source.lean.txt").write_text("changed\n")
        with self.assertRaisesRegex(ValueError, "altered receipt file"):
            verify(self.root)

    def test_missing_development_attempt(self) -> None:
        lean = self.root / "lean"
        shutil.copytree(HERE / "lean/development", lean / "development",
                        ignore=shutil.ignore_patterns("*.olean"))
        shutil.copytree(HERE / "lean/audit-development", lean / "audit-development",
                        ignore=shutil.ignore_patterns("*.olean"))
        shutil.copy2(HERE / "DEVELOPMENT_INVENTORY.json", self.root)
        verify_development(self.root)
        (lean / "development/001/ArchiveModel.stdout").unlink()
        with self.assertRaisesRegex(ValueError, "development file coverage changed"):
            verify_development(self.root)


if __name__ == "__main__":
    unittest.main()
