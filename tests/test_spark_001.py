"""SPARK-001 independent Python oracle tests. SPDX-License-Identifier: MPL-2.0"""
from __future__ import annotations

import unittest

from scripts.verify_spark_001 import interval_oracle, parse_oracle, vectors


class SparkReferenceTests(unittest.TestCase):
    def test_decimal_boundaries_and_invalid_input(self) -> None:
        for source, expected in (
            ("9999.99", "OK 999999"),
            ("-9999.99", "OK -999999"),
            ("-0.00", "OK 0"),
            ("00.00", "INVALID"),
            ("1e2", "INVALID"),
            ("10000.00", "INVALID"),
            ("NaN", "INVALID"),
            ("", "INVALID"),
        ):
            with self.subTest(source=source):
                self.assertEqual(parse_oracle(source), expected)

    def test_closed_intervals_and_zero_missinguess(self) -> None:
        self.assertEqual(interval_oracle(1, 0, 1, 1, 1, 2), "OVERLAP")
        self.assertEqual(interval_oracle(1, 0, 1, 1, 2, 3), "BELOW")
        self.assertEqual(interval_oracle(1, 2, 3, 1, 0, 1), "ABOVE")
        self.assertEqual(interval_oracle(0, 0, 0, 2, 0, 0), "MISSING")
        self.assertEqual(interval_oracle(2, 0, 0, 1, 0, 0), "OVERLAP")
        self.assertEqual(interval_oracle(2, 1, 1, 1, 0, 0), "INVALID")

    def test_local_proof_is_only_owner_authorized_main_dispatch(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        source = (root / ".github/workflows/spark-001-proof.yml").read_text()
        self.assertIn("workflow_dispatch:", source)
        self.assertIn("github.ref == 'refs/heads/main'", source)
        self.assertIn("github.actor == 'EmergentMonk'", source)
        self.assertIn("inputs.authorize_proof == true", source)
        self.assertIn("persist-credentials: false", source)
        self.assertNotIn("  pull_request:", source)
        self.assertNotIn("  push:", source)

    def test_local_proof_fails_on_unproved_checks_and_warnings(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/spark-001-proof.yml").read_text()
        proof_step = workflow.split("      - name: Run GNATprove", 1)[1].split(
            "      - name: Record proof receipt", 1
        )[0]
        self.assertIn("set -euo pipefail", proof_step)
        self.assertIn("gnatprove -P verification/spark/spark_core.gpr", proof_step)
        self.assertIn("--mode=all", proof_step)
        self.assertIn("--checks-as-errors=on", proof_step)
        self.assertIn("--warnings=error", proof_step)
        self.assertIn("--proof-warnings=on", proof_step)
        self.assertIn("--report=statistics", proof_step)
        self.assertNotIn("|| true", proof_step)
        self.assertNotIn("continue-on-error: true", proof_step)
        self.assertIn("steps.prove.conclusion", workflow)
        self.assertIn("PROOF.log RESULT.txt > SHA256SUMS", workflow)

    def test_fixed_seed_vectors_and_source_identities(self) -> None:
        result = vectors()
        self.assertEqual(result, vectors())
        self.assertGreater(len(result), 300)
        self.assertEqual(len([x for x in result if x[0].startswith("L ")]), 11)
        self.assertTrue(all(isinstance(z, str) for pair in result for z in pair))


if __name__ == "__main__":
    unittest.main()
