"""SPARK-002 Phase 1B oracle and boundary tests. SPDX-License-Identifier: MPL-2.0"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from scripts.verify_spark_002_phase_1b import (
    SEED,
    packet_command,
    packet_oracle,
    reading_oracle,
    valid_rows,
    vectors,
    verify,
)

ROOT = Path(__file__).resolve().parents[1]


class PartitionOracleTests(unittest.TestCase):
    def test_all_supported_packet_lengths(self) -> None:
        for count in (2, 3, 4):
            with self.subTest(campaigns=count):
                rows = valid_rows(count)
                self.assertEqual(len(rows), count * 2)
                self.assertEqual(packet_oracle(rows), "STRUCTURAL_ONLY_UNAUTHENTICATED")
        self.assertEqual(packet_oracle([]), "BLOCKED")
        self.assertEqual(packet_oracle(valid_rows()[:3]), "BLOCKED")

    def test_duplicate_row_id_and_empty_identity_rejected(self) -> None:
        original = valid_rows()
        for field in ("rid", "camp", "lab", "run", "doc", "measure",
                      "diagnostic", "event", "registration"):
            with self.subTest(field=field):
                rows = original.copy()
                rows[1] = replace(rows[1], **{field: 0})
                self.assertEqual(packet_oracle(rows), "BLOCKED")
        rows = original.copy()
        rows[1] = replace(rows[1], rid=rows[0].rid)
        self.assertEqual(packet_oracle(rows), "BLOCKED")

    def test_whole_campaign_train_holdout_and_lab_leakage(self) -> None:
        original = valid_rows()
        rows = original.copy()
        for index in (2, 3):
            rows[index] = replace(rows[index], camp=original[0].camp)
        self.assertEqual(packet_oracle(rows), "BLOCKED")
        rows = original.copy()
        for index in (2, 3):
            rows[index] = replace(rows[index], lab=original[0].lab)
        self.assertEqual(packet_oracle(rows), "BLOCKED")
        rows = original.copy()
        rows[1] = replace(rows[1], role=1)
        self.assertEqual(packet_oracle(rows), "BLOCKED")

    def test_source_reuse_for_every_provenance_dimension(self) -> None:
        original = valid_rows()
        for field in ("run", "doc", "measure", "diagnostic", "event"):
            with self.subTest(field=field):
                rows = original.copy()
                for index in (2, 3):
                    rows[index] = replace(rows[index], **{field: getattr(original[0], field)})
                self.assertEqual(packet_oracle(rows), "BLOCKED")
        rows = original.copy()
        for index in (2, 3):
            rows[index] = replace(rows[index], diagnostic=original[0].measure)
        self.assertEqual(packet_oracle(rows), "BLOCKED")

    def test_same_campaign_diagnostic_reuse_permitted(self) -> None:
        rows = valid_rows()
        self.assertEqual(rows[0].diagnostic, rows[1].diagnostic)
        self.assertEqual(rows[0].event, rows[1].event)
        self.assertEqual(packet_oracle(rows), "STRUCTURAL_ONLY_UNAUTHENTICATED")

    def test_missing_or_duplicate_phase_and_registration_rejected(self) -> None:
        rows = valid_rows()
        rows[1] = replace(rows[1], phase=0)
        self.assertEqual(packet_oracle(rows), "BLOCKED")
        rows = valid_rows()
        rows[3] = replace(rows[3], registration=901)
        self.assertEqual(packet_oracle(rows), "BLOCKED")

    def test_zero_uncertainty_diagnostic_and_synthetic_fail_closed(self) -> None:
        for field, value in (
            ("error", 0), ("diag_error", 0), ("source", 1),
            ("source", 2), ("source", 3), ("conditions", 0),
            ("reading", 2), ("reading", 3),
        ):
            with self.subTest(field=field, value=value):
                rows = valid_rows()
                rows[0] = replace(rows[0], **{field: value})
                self.assertEqual(packet_oracle(rows), "BLOCKED")

    def test_missingness_boundary_zero_and_invalid_precedence(self) -> None:
        self.assertEqual(reading_oracle(0, 0, 1, 0), "EQUAL")
        self.assertEqual(reading_oracle(0, -1, 1, 0), "BELOW")
        self.assertEqual(reading_oracle(1, 0, 0, -1), "ABOVE")
        self.assertEqual(reading_oracle(2, 0, 0, 0), "MISSING_INPUT")
        self.assertEqual(reading_oracle(3, 0, 2, 0), "INVALID_INPUT")
        self.assertEqual(reading_oracle(1, 1, 2, 0), "INVALID_INPUT")
        self.assertEqual(reading_oracle(0, 1_000_001, 1, 0), "INVALID")
        rows = valid_rows()
        rows[1] = replace(rows[1], value=1)
        self.assertEqual(packet_oracle(rows), "BLOCKED")

    def test_padding_and_out_of_range_fail_closed(self) -> None:
        self.assertEqual(packet_oracle(valid_rows(), tampered_tail=True), "BLOCKED")
        self.assertEqual(packet_oracle(valid_rows(4), tampered_tail=True), "INVALID")
        rows = valid_rows()
        rows[0] = replace(rows[0], rid=65_536)
        self.assertEqual(packet_oracle(rows), "INVALID")
        self.assertEqual(packet_oracle([*valid_rows(4), valid_rows()[0]]), "INVALID")

    def test_deterministic_reference_vector_corpus(self) -> None:
        corpus = vectors()
        self.assertEqual(corpus, vectors())
        self.assertGreater(len(corpus), 1_000)
        self.assertEqual(SEED, 20261110)
        self.assertIn((packet_command(valid_rows()),
                       "STRUCTURAL_ONLY_UNAUTHENTICATED"), corpus)
        self.assertIn(("O 2 0 3 0", "INVALID_INPUT"), corpus)
        self.assertFalse(any(expected == "UNSAFE" for _, expected in corpus))

    def test_executable_validation_and_shell_free_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                verify(Path(directory) / "missing")
            f = Path(directory) / "not-executable"
            f.write_text("not a probe")
            with self.assertRaisesRegex(ValueError, "executable regular file"):
                verify(f)
        transcript = "\n".join(expected for _, expected in vectors()) + "\n"
        with mock.patch(
            "scripts.verify_spark_002_phase_1b.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, transcript, ""),
        ) as run:
            result = verify(Path(sys.executable))
        self.assertEqual(result["vectors"], len(vectors()))
        self.assertIs(result["physical_evidence_admitted"], False)
        self.assertEqual(result["gnatprove"], "NOT_INVOKED_BY_DIFFERENTIAL_TEST")
        self.assertIs(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.args[0], [str(Path(sys.executable).resolve())])

    def test_isolated_spark_units_and_hosted_ci_only(self) -> None:
        spec = (ROOT / "verification/spark002/phase1b/spark_002_partition.ads").read_text()
        workflow = (ROOT / ".github/workflows/spark-002-phase-1b.yml").read_text()
        self.assertIn("SPARK_Mode => On", spec)
        self.assertIn("Packet_Eligible", spec)
        self.assertIn("for all I in Row_Index", spec)
        self.assertIn("Structural_Only_Unauthenticated", spec)
        self.assertIn("NOT_EXECUTED", workflow)
        self.assertIn("gnatmake-13", workflow)
        self.assertNotIn("self-hosted", workflow)
        self.assertNotIn("continue-on-error", workflow)


if __name__ == "__main__":
    unittest.main()
