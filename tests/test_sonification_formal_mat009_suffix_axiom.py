"""Bind the retained compiler-suffix bypass to its repaired Lean rejection."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from formal.sonification.mat009.lean.verify_repair import CORRECTED, ORIGINAL, verify


class Mat009SuffixAxiomTests(unittest.TestCase):
    def test_original_accepts_and_repaired_gate_rejects(self) -> None:
        result = verify()
        self.assertTrue(result["vulnerable_gate_accepted"])
        self.assertTrue(result["corrected_gate_rejected"])
        self.assertEqual(result["detected"], 7)

    def test_missing_rejection_log_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mat009-suffix-receipt-") as temp:
            copied = Path(temp) / "corrected"
            shutil.copytree(CORRECTED, copied)
            (copied / "compiler_suffix_false_axiom/build-04-LeanAudit.stdout").unlink()
            with self.assertRaisesRegex(ValueError, "evidence file inventory changed"):
                verify(ORIGINAL, copied)


if __name__ == "__main__":
    unittest.main()
