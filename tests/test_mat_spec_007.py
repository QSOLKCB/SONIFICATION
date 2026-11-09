"""MAT-SPEC-007: published experiment-family fit/lineage preservation.

SPDX-License-Identifier: MPL-2.0
"""
from __future__ import annotations

import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from materials import mat_spec, mat_spec_006, mat_spec_007

ROOT = Path(__file__).resolve().parents[1]


class FitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = mat_spec.read_regular(ROOT / mat_spec_007.SOURCE_PATH)
        cls.rows = mat_spec_007.parse_source(cls.raw)
        cls.pairs, cls.counts = mat_spec_007.pairwise_fits(cls.rows)

    def test_source_identity_does_not_count_papers_as_new_experiments(self) -> None:
        self.assertEqual(len(self.rows), 4)
        self.assertEqual(
            {row["reference_condition"] for row in self.rows},
            {"HE4_SVP"},
        )
        self.assertEqual(
            len({r["acquisition_campaign"] for r in self.rows}), 4
        )
        self.assertEqual(len({r["lab_family"] for r in self.rows}), 3)
        self.assertNotEqual(
            self.rows[0]["analysis_doi"], self.rows[0]["measurement_doi"]
        )
        self.assertNotEqual(
            self.rows[1]["analysis_doi"], self.rows[1]["measurement_doi"]
        )
        self.assertEqual(
            self.rows[2]["lab_family"], self.rows[3]["lab_family"]
        )
        self.assertNotEqual(
            self.rows[2]["acquisition_campaign"],
            self.rows[3]["acquisition_campaign"],
        )

    def test_reported_fit_values_and_uncertainty_boxes(self) -> None:
        self.assertEqual(
            [(r["alpha"], r["alpha_reported_error"]) for r in self.rows],
            [
                ("-0.016", "0.002"), ("-0.0198", "0.0037"),
                ("-0.0127", "0.0026"), ("-0.0127", "0.0003"),
            ],
        )
        self.assertEqual(
            mat_spec_007.interval(self.rows[1], "alpha"),
            (Fraction("-0.0235"), Fraction("-0.0161")),
        )
        self.assertEqual(
            mat_spec_007.interval(self.rows[-1], "amplitude_ratio"),
            (Fraction("1.051"), Fraction("1.055")),
        )
        with self.assertRaises(ValueError):
            mat_spec_007.interval(self.rows[0], "temperature")

    def test_six_cross_campaign_pairs_and_honest_disagreement(self) -> None:
        self.assertEqual(len(self.pairs), 6)
        self.assertEqual(
            self.counts["relations"]["alpha"],
            {"a_below_b": 3, "b_below_a": 0, "overlap": 3},
        )
        self.assertEqual(
            self.counts["relations"]["amplitude_ratio"],
            {"a_below_b": 0, "b_below_a": 2, "overlap": 4},
        )
        self.assertEqual(self.counts["cross_lab_family_pairs"], 5)
        self.assertEqual(self.counts["same_lab_distinct_campaign_pairs"], 1)
        self.assertTrue(self.counts["closed_error_boxes_not_confidence_intervals"]) if (
            "closed_error_boxes_not_confidence_intervals" in self.counts
        ) else self.assertEqual(
            self.counts["statistical_significance"], "NOT_TESTED"
        )

    def test_closed_boundary_rescaling_and_reversal(self) -> None:
        a = (Fraction(1), Fraction(2))
        b = (Fraction(2), Fraction(3))
        self.assertEqual(mat_spec_007.classify(a, b), "overlap")
        b = (Fraction("2.0001"), Fraction(3))
        self.assertEqual(mat_spec_007.classify(a, b), "a_below_b")
        self.assertEqual(mat_spec_007.classify(b, a), "b_below_a")
        self.assertEqual(
            mat_spec_007.classify(
                tuple(2 * p for p in a), tuple(2 * p for p in b)
            ),
            "a_below_b",
        )
        with self.assertRaises(ValueError):
            mat_spec_007.classify((Fraction(2), Fraction(1)), b)

    def test_source_tamper_and_invalid_decimals_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            mat_spec_007.parse_source(
                self.raw.replace(b"-0.0198", b"-0.0199")
            )
        for item in ("NaN", "1e5", "1/3", " 0.1", "-00.1", "", "inf"):
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    mat_spec_007.decimal(item)
        for item in ("-1", "0"):
            with self.assertRaises(ValueError):
                mat_spec_007.decimal(item, positive=True)

    def test_symbolic_ratio_receiver_not_signed_alpha(self) -> None:
        result = mat_spec_007.receiver_audit(self.rows)
        self.assertEqual(result["exact_ratio_count"], 4)
        self.assertEqual(result["midi_note_count"], 2)
        self.assertEqual(result["midi_colliding_pairs"], 3)
        self.assertEqual(
            [r["nearest_midi_note"] for r in result["profiles"]],
            [68, 69, 68, 68],
        )
        self.assertTrue(result["alpha_signed_exponent_not_pitched"])
        self.assertEqual(result["listener_test"], "NOT_PERFORMED")

    def test_lineage_gate_is_not_an_independent_phase_classifier(self) -> None:
        result = mat_spec_007.gate(self.rows, self.counts)
        self.assertEqual(result["status"], "PUBLISHED_FIT_CONCORDANCE_ONLY")
        self.assertEqual(result["different_lab_families"], 3)
        self.assertEqual(result["raw_measurement_replication"], "NOT_PERFORMED")
        self.assertEqual(result["phase_classifier_training"], "NOT_PERFORMED")
        self.assertIsNone(result["phase_classifier_heldout_score"])


class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = mat_spec_007.build_evidence(ROOT)
        cls.manifest = json.loads(cls.bundle["manifest.json"])

    def test_deterministic_artifacts_and_parent_receipts(self) -> None:
        self.assertEqual(set(self.bundle), mat_spec_007.OUTPUT_NAMES)
        self.assertEqual(self.bundle, mat_spec_007.build_evidence(ROOT))
        self.assertEqual(self.manifest["profile"], mat_spec_007.PROFILE)
        self.assertEqual(
            self.manifest["source"]["sha256"], mat_spec_007.SOURCE_SHA256
        )
        self.assertIsNone(self.manifest["canonical_pcm_sha256"])
        self.assertIsNone(self.manifest["canonical_wav_sha256"])
        self.assertFalse(self.manifest["audio_generated"])
        parent = mat_spec_006.build_evidence(ROOT)
        self.assertEqual(set(parent), set(self.manifest["parent_artifacts"]))
        for name, record in self.manifest["parent_artifacts"].items():
            self.assertEqual(mat_spec.sha256(parent[name]), record["sha256"])
        for name, record in self.manifest["outputs"].items():
            self.assertEqual(mat_spec.sha256(self.bundle[name]), record["sha256"])
        self.assertEqual(len(list(csv.DictReader(io.StringIO(
            self.bundle["pair-relations.csv"].decode("ascii")
        )))), 6)

    def test_drifted_contract_metadata_and_parent_are_rejected(self) -> None:
        native = mat_spec.read_regular

        def changed(path: Path, limit: int = 1_048_576) -> bytes:
            raw = native(path, limit)
            if path.name == "mat-spec-007.v0.1.json":
                return raw.replace(b'"version": "0.1.0"', b'"version": "0.9.0"')
            return raw

        with (
            patch("materials.mat_spec_007.mat_spec.read_regular", side_effect=changed),
            self.assertRaisesRegex(ValueError, "frozen"),
        ):
            mat_spec_007.build_evidence(ROOT)
        native_parent = mat_spec_006.build_evidence(ROOT)
        altered = dict(native_parent)
        altered["phase-gate.json"] = b"counterfeit"
        with (
            patch("materials.mat_spec_007.mat_spec_006.build_evidence", return_value=altered),
            self.assertRaises(ValueError),
        ):
            mat_spec_007.build_evidence(ROOT)
        altered = dict(native_parent)
        altered["extra.json"] = b"unexpected"
        with (
            patch("materials.mat_spec_007.mat_spec_006.build_evidence", return_value=altered),
            self.assertRaisesRegex(ValueError, "membership"),
        ):
            mat_spec_007.build_evidence(ROOT)

    def test_no_follow_symbolic_export_and_no_audio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = mat_spec_007.write_evidence(root, "dist/result", self.bundle)
            self.assertEqual(set(p.name for p in output.iterdir()), mat_spec_007.OUTPUT_NAMES)
            with self.assertRaises(FileExistsError):
                mat_spec_007.write_evidence(root, "dist/result", self.bundle)
            outside = root / "outside"
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                mat_spec_007.write_evidence(root, "link/escape", self.bundle)
            self.assertEqual(list(outside.iterdir()), [])
            for invalid in ("", "../oops", "/abs", "a//b", "a/../b"):
                with self.assertRaises(ValueError):
                    mat_spec_007.write_evidence(root, invalid, self.bundle)
            with self.assertRaises(ValueError):
                mat_spec_007.write_evidence(root, "audio", {"sound.wav": b""})
        for args in (["--render-audio"], ["--format", "wav"]):
            p = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_mat_spec_007.py"), *args],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(p.returncode, 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX only")
    def test_symlink_and_fifo_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "source.csv").symlink_to(ROOT / mat_spec_007.SOURCE_PATH)
            with self.assertRaises(OSError):
                mat_spec.read_regular(root / "source.csv")
            os.mkfifo(root / "pipe")
            with self.assertRaises(ValueError):
                mat_spec.read_regular(root / "pipe")


if __name__ == "__main__":
    unittest.main()
