"""SPARK-002 bounded independent oracle checks. SPDX-License-Identifier: MPL-2.0."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.verify_spark_002 import (
    gate_oracle,
    interval_oracle,
    provenance_oracle,
    scale_oracle,
    vectors,
    verify,
)

ROOT = Path(__file__).resolve().parents[1]


class Spark002Oracle(unittest.TestCase):
    def test_mat_spec_007_closed_intervals(self) -> None:
        self.assertEqual(interval_oracle(0, 1, 2, 1), "OVERLAP")
        self.assertEqual(interval_oracle(-5, 0, 5, 0), "A_BELOW_B")
        self.assertEqual(interval_oracle(5, 0, -5, 0), "B_BELOW_A")
        self.assertEqual(interval_oracle(0, 0, 0, 0), "OVERLAP")
        self.assertEqual(interval_oracle(4_000_001, 0, 0, 0), "INVALID")
        self.assertEqual(interval_oracle(0, -1, 0, 0), "INVALID")

    def test_positive_scaling_and_invalid_factor(self) -> None:
        for args in ((0, 1, 2, 1), (-5, 0, 5, 0), (5, 0, -5, 0)):
            for factor in (1, 2, 8):
                self.assertEqual(scale_oracle(*args, factor), "TRUE")
        self.assertEqual(scale_oracle(0, 1, 2, 1, 0), "INVALID")
        self.assertEqual(scale_oracle(0, 1, 2, 1, 9), "INVALID")

    def test_source_class_and_missing_gate_fail_closed(self) -> None:
        self.assertEqual(gate_oracle(0, 31, 2, 1, 1, 1),
                         "STRUCTURAL_ONLY_UNAUTHENTICATED")
        for kind in range(1, 7):
            self.assertEqual(gate_oracle(kind, 31, 2, 1, 1, 1), "BLOCKED")
        for mask in (0, 15, 23, 30):
            self.assertEqual(gate_oracle(0, mask, 2, 1, 1, 1), "BLOCKED")
        for counts in ((1, 0, 0, 0), (2, 0, 1, 1), (2, 1, 0, 1), (2, 1, 1, 0)):
            self.assertEqual(gate_oracle(0, 31, *counts), "BLOCKED")

    def test_provenance_code_separation(self) -> None:
        self.assertEqual(provenance_oracle(1), "TRUE")
        for mode in range(2, 12):
            self.assertEqual(provenance_oracle(mode), "FALSE")
        self.assertEqual(provenance_oracle(12), "INVALID")

    def test_vectors_deterministic_and_adversarial(self) -> None:
        self.assertEqual(vectors(), vectors())
        self.assertGreater(len(vectors()), 1_000)
        self.assertIn(("F", "BLOCKED_NO_SCORE"), vectors())
        self.assertIn(("G 4 31 4 6 4 4", "BLOCKED"), vectors())

    def test_probe_caller_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            with self.assertRaises(FileNotFoundError):
                verify(missing)
            nonexec = Path(tmp) / "nonexec"
            nonexec.write_text("no")
            with self.assertRaisesRegex(ValueError, "not executable"):
                verify(nonexec)

    def test_probe_is_shell_free(self) -> None:
        stdout = "\n".join(answer for _, answer in vectors()) + "\n"
        with mock.patch(
            "scripts.verify_spark_002.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, stdout, ""),
        ) as mocked:
            receipt = verify(Path(sys.executable))
        self.assertEqual(receipt["status"], "EXECUTED_ADA_PYTHON_DIFFERENTIAL_PASS")
        self.assertEqual(receipt["physical_evidence_admitted"], False)
        self.assertEqual(receipt["gnatprove"], "NOT_INVOKED_BY_DIFFERENTIAL_TEST")
        self.assertIs(mocked.call_args.kwargs["shell"], False)
        self.assertEqual(mocked.call_args.args[0], [str(Path(sys.executable).resolve())])

    def test_separate_kernel_and_proof_boundary(self) -> None:
        spec = (ROOT / "verification/spark002/spark_002_core.ads").read_text()
        driver = (ROOT / "verification/spark002/spark_002_probe.adb").read_text()
        self.assertIn("SPARK_Mode => On", spec)
        self.assertIn("Original_Processed", spec)
        self.assertIn("Structural_Only_Unauthenticated", spec)
        self.assertIn("Classifier_Score_Available", spec)
        self.assertIn("Pair_Separated", spec)
        self.assertIn("Non-SPARK differential CLI", driver)

    def test_workflow_scope(self) -> None:
        workflow = (ROOT / ".github/workflows/spark-002.yml").read_text()
        self.assertIn("gnatmake-13", workflow)
        self.assertIn("verification/spark002/", workflow)
        self.assertIn("scripts/verify_spark_002.py", workflow)
        self.assertIn("NOT_EXECUTED", workflow)
        self.assertNotIn("self-hosted", workflow)
        self.assertNotIn("continue-on-error", workflow)
        self.assertNotIn("--render-audio", workflow)


if __name__ == "__main__":
    unittest.main()
