"""Mutation-archive integrity controls for MAT009 model evidence."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from formal.sonification.mat009.lean.verify_negative import DEFAULT_ARCHIVE, verify


class Mat009NegativeReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mat009-negative-receipt-control-")
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "negative"
        shutil.copytree(DEFAULT_ARCHIVE, self.archive)

    def test_intact_archive(self) -> None:
        result = verify(self.archive)
        self.assertEqual(result["status"], "MAT009_NEGATIVE_EVIDENCE_BOUND")
        self.assertEqual(result["detected"], 6)

    def test_missing_mutant_source(self) -> None:
        (self.archive / "003/weaken_final_leakage_theorem/mutant-source.lean.txt").unlink()
        with self.assertRaisesRegex(ValueError, "archive file inventory changed"):
            verify(self.archive)

    def test_altered_failed_proof_log(self) -> None:
        log = self.archive / "003/prohibited_project_axiom/build-04-LeanAudit.stdout"
        log.write_text("project axiom declaration detected\n")
        with self.assertRaisesRegex(ValueError, "altered negative evidence"):
            verify(self.archive)

    def test_missing_prior_failure_receipt(self) -> None:
        (self.archive / "002/result.json").unlink()
        with self.assertRaisesRegex(ValueError, "archive file inventory changed"):
            verify(self.archive)


if __name__ == "__main__":
    unittest.main()
