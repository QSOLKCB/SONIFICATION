"""Fail-closed controls for the retained MAT009 Lean proof receipt."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from formal.sonification.mat009.lean import verify as lean_verify


class Mat009LeanReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mat009-lean-receipt-control-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.attempt = self.root / "attempt"
        shutil.copytree(lean_verify.DEFAULT_ATTEMPT, self.attempt)

    def proof_copy(self) -> Path:
        proof = self.root / "proof"
        proof.mkdir()
        for name in lean_verify.INPUTS:
            shutil.copyfile(lean_verify.HERE / name, proof / name)
        return proof

    def test_intact_receipt(self) -> None:
        result = lean_verify.verify(self.attempt)
        self.assertEqual(result["status"], "MAT009_LEAN_EVIDENCE_BOUND")
        self.assertEqual(result["REFINEMENT_PROVED"], "OPEN")

    def test_removed_build_log(self) -> None:
        (self.attempt / "build-04-LeanAudit.stdout").unlink()
        with self.assertRaisesRegex(ValueError, "evidence file inventory changed"):
            lean_verify.verify(self.attempt)

    def test_altered_build_stderr(self) -> None:
        (self.attempt / "build-03-ExactTypes.stderr").write_text("invented success\n")
        with self.assertRaisesRegex(ValueError, "altered evidence file"):
            lean_verify.verify(self.attempt)

    def test_removed_toolchain_import_receipt(self) -> None:
        (self.attempt / "toolchain-imports.json").unlink()
        with self.assertRaisesRegex(ValueError, "evidence file inventory changed"):
            lean_verify.verify(self.attempt)

    def test_altered_model_assurance(self) -> None:
        result = self.attempt / "result.json"
        result.write_text(result.read_text().replace('"REFINEMENT_PROVED": "OPEN"',
                                                     '"REFINEMENT_PROVED": "PASS"'))
        with self.assertRaisesRegex(ValueError, "altered evidence file"):
            lean_verify.verify(self.attempt)

    def test_altered_theorem_type_inventory(self) -> None:
        types = self.attempt / "theorem-types.json"
        types.write_text(types.read_text().replace("MAT009.M009_R1_initial", "False"))
        with self.assertRaisesRegex(ValueError, "altered evidence file"):
            lean_verify.verify(self.attempt)

    def test_stale_proof_source(self) -> None:
        proof = self.proof_copy()
        source = proof / "SplitModel.lean"
        source.write_text(source.read_text() + "\n-- unexpected source edit\n")
        with (
            patch.object(lean_verify, "HERE", proof),
            self.assertRaisesRegex(ValueError, "stale proof source"),
        ):
            lean_verify.verify(self.attempt)

    def test_unimported_failing_module(self) -> None:
        proof = self.proof_copy()
        (proof / "Unimported.lean").write_text("theorem hidden_false : False := by trivial\n")
        with (
            patch.object(lean_verify, "HERE", proof),
            self.assertRaisesRegex(ValueError, "proof module coverage changed"),
        ):
            lean_verify.verify(self.attempt)

    def test_wrong_toolchain_binary(self) -> None:
        with self.assertRaisesRegex(ValueError, "installed Lean executable changed"):
            lean_verify.verify(self.attempt, Path("/bin/true"))


if __name__ == "__main__":
    unittest.main()
