"""MAT-SPEC-006: experiment provenance, phase holdout and security tests.

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

from materials import mat_spec, mat_spec_005, mat_spec_006

ROOT = Path(__file__).resolve().parents[1]


def fixture(source: str, family: str, split: str, phase: str) -> dict:
    return {
        "row_id": source + ":" + phase,
        "source_id": source,
        "experimental_family_id": family,
        "split": split,
        "phase": phase,
        "label_basis": "INDEPENDENT_PHYSICAL_DIAGNOSTIC",
        "diagnostic_type": "SECOND_SOUND_DIRECT_DETECTION",
        "measurement_uncertainty": "0.1",
        "diagnostic_uncertainty": "0.02",
        "pressure_condition": "SATURATED_VAPOUR_PRESSURE_HELIUM_4",
        "provenance_hash": "f" * 64,
        "synthetic_fixture": True,
    }


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original = mat_spec.read_regular(ROOT / mat_spec_006.DATA_PATH)
        cls.rows = mat_spec_006.parse_measurements(cls.original)
        cls.receiver = mat_spec_006.map_receivers(cls.rows)

    def test_visual_checked_table_values_and_signed_offsets(self) -> None:
        self.assertEqual(len(self.rows), 12)
        self.assertEqual(self.rows[0]["delta_T_microkelvin"], "-0.593")
        self.assertEqual(self.rows[0]["heat_capacity_J_per_mol_K"], "91.23")
        self.assertEqual(self.rows[5]["delta_T_microkelvin"], "-0.029")
        self.assertEqual(self.rows[5]["heat_capacity_J_per_mol_K"], "105.50")
        self.assertEqual(self.rows[6]["delta_T_microkelvin"], "0.075")
        self.assertEqual(self.rows[6]["heat_capacity_J_per_mol_K"], "82.04")
        self.assertEqual(self.rows[-1]["heat_capacity_J_per_mol_K"], "70.78")
        for row in self.rows:
            self.assertIsNone(row["temperature_absolute_K"])
            self.assertIsNone(row["row_uncertainty_J_per_mol_K"])
            self.assertFalse(row["source_table_side_is_independent_label"])
        self.assertEqual(
            set(r["source_campaign_id"] for r in self.rows),
            {mat_spec_006.CAMPAIGN},
        )

    def test_binary_source_mutation_rejected_and_bad_numbers(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            mat_spec_006.parse_measurements(
                self.original.replace(b"105.50", b"105.51")
            )
        for number in ("-1", "NaN", "1/2", "1e5", " 2", "01.2"):
            with self.assertRaises(ValueError):
                mat_spec_006._decimal(number)
        for wrong in (Fraction(0), Fraction(-1), 2, 0.5):
            with self.assertRaises(ValueError):
                mat_spec_006.map_receivers(self.rows, wrong)

    def test_exact_receiver_and_sample_bias_limitation(self) -> None:
        audit = mat_spec_006.source_numerical_audit(self.rows, self.receiver)
        self.assertEqual(audit["measured_and_processed_source_rows"], 12)
        self.assertEqual(audit["below_context_rows"], 6)
        self.assertEqual(audit["above_context_rows"], 6)
        self.assertEqual(audit["exact_fraction_roundtrip_checks"], 12)
        self.assertEqual(
            Fraction(audit["closest_selected_heat_capacity_difference_J_mol_K"]),
            Fraction(-1173, 50),
        )
        self.assertFalse(audit["near_pair_offsets_equal_magnitude"])
        self.assertFalse(audit["infer_transition_jump_or_significance"])
        self.assertEqual(audit["distinct_reported_values"], 12)
        self.assertEqual(audit["receiver_distinct_midi_notes"], 7)
        self.assertEqual(audit["receiver_colliding_row_pairs"], 7)
        shifted = [dict(r) for r in self.receiver]
        shifted[0]["frequency_target_Hz"] = "999"
        with self.assertRaisesRegex(ValueError, "roundtrip"):
            mat_spec_006.source_numerical_audit(self.rows, shifted)

    def test_positive_scale_preserves_fraction_identity_and_midi_is_not_physics(self) -> None:
        alternative = mat_spec_006.map_receivers(self.rows, Fraction(10))
        for left, right in zip(self.receiver, alternative, strict=True):
            self.assertEqual(
                2 * Fraction(left["frequency_target_Hz"]),
                Fraction(right["frequency_target_Hz"]),
            )
        self.assertTrue(all("phase_label_provenance" in r for r in alternative))


class SplitProtocolTests(unittest.TestCase):
    @staticmethod
    def rows() -> list[dict]:
        return [
            fixture("TRAIN_LAB", "FAMILY_A", "TRAIN", "HE_I"),
            fixture("TRAIN_LAB", "FAMILY_A", "TRAIN", "HE_II"),
            fixture("TEST_LAB", "FAMILY_B", "HOLDOUT", "HE_I"),
            fixture("TEST_LAB", "FAMILY_B", "HOLDOUT", "HE_II"),
        ]

    def test_synthetic_structural_fixture_never_earns_empirical_status(self) -> None:
        result = mat_spec_006.check_future_split_structure(self.rows())
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reasons"], ["SYNTHETIC_NOT_PHYSICAL_EVIDENCE"])
        self.assertIsNone(result["holdout_accuracy"])
        self.assertFalse(result["physical_validation_admitted"])
        unsigned = [dict(r) for r in self.rows()]
        for row in unsigned:
            row.pop("synthetic_fixture")
        structural = mat_spec_006.check_future_split_structure(unsigned)
        self.assertEqual(structural["status"], "STRUCTURAL_ONLY_NOT_EMPIRICAL_ADMISSION")
        self.assertFalse(structural["independence_authenticated"])
        self.assertIsNone(structural["holdout_accuracy"])

    def test_source_leakage_and_diagnostic_label_circularity(self) -> None:
        cases = [
            (lambda rows: rows[2].update(experimental_family_id="FAMILY_A"),
             "SOURCE_LINEAGE_LEAKAGE"),
            (lambda rows: rows[2].update(source_id="TRAIN_LAB"),
             "SOURCE_LINEAGE_LEAKAGE"),
            (lambda rows: rows[2].update(label_basis="TEMPERATURE_THRESHOLD"),
             "CIRCULAR_OR_UNVERIFIED_PHASE_LABEL"),
            (lambda rows: rows[2].update(diagnostic_type="LOOKUP_LAMBDA_T"),
             "CIRCULAR_OR_UNVERIFIED_PHASE_LABEL"),
            (lambda rows: rows[2].update(measurement_uncertainty=None),
             "MISSING_POSITIVE_CALIBRATED_UNCERTAINTY"),
            (lambda rows: rows[2].update(diagnostic_uncertainty="0"),
             "MISSING_POSITIVE_CALIBRATED_UNCERTAINTY"),
            (lambda rows: rows[2].update(provenance_hash="bad"),
             "UNBOUND_PHYSICAL_CONDITIONS_OR_PROVENANCE"),
        ]
        for alter, reason in cases:
            rows = self.rows()
            for row in rows:
                row.pop("synthetic_fixture")
            alter(rows)
            gate = mat_spec_006.check_future_split_structure(rows)
            self.assertIn(reason, gate["reasons"])
            self.assertEqual(gate["status"], "BLOCKED")
            self.assertIsNone(gate["holdout_accuracy"])
        self.assertEqual(
            mat_spec_006.check_future_split_structure([])["reasons"],
            ["EMPTY_CANDIDATE"],
        )

    def test_rejects_empty_whitespace_and_malformed_source_identities(self) -> None:
        # Reproduce the reviewer finding: both TRAIN identifiers are empty.
        rows = self.rows()
        for row in rows:
            row.pop("synthetic_fixture")
        for row in rows[:2]:
            row["source_id"] = ""
            row["experimental_family_id"] = ""
        result = mat_spec_006.check_future_split_structure(rows)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["reasons"], ["MISSING_SOURCE_IDENTITY"])
        self.assertFalse(result["physical_validation_admitted"])
        self.assertIsNone(result["holdout_accuracy"])

        # Exercise each identity dimension independently, including nonstrings.
        for field in ("source_id", "experimental_family_id"):
            for invalid in ("", " \t\n", None, [], 0, " PADDED "):
                with self.subTest(field=field, invalid=invalid):
                    candidate = self.rows()
                    for row in candidate:
                        row.pop("synthetic_fixture")
                    for row in candidate[:2]:
                        row[field] = invalid
                    outcome = mat_spec_006.check_future_split_structure(candidate)
                    self.assertEqual(outcome["status"], "BLOCKED")
                    self.assertIn("MISSING_SOURCE_IDENTITY", outcome["reasons"])
                    self.assertFalse(outcome["independence_authenticated"])
                    self.assertIsNone(outcome["holdout_accuracy"])

    def test_no_row_random_split_or_single_phase_holdout(self) -> None:
        rows = self.rows()
        for row in rows:
            row.pop("synthetic_fixture")
        rows[3]["phase"] = "HE_I"
        result = mat_spec_006.check_future_split_structure(rows)
        self.assertIn("HOLDOUT_REQUIRES_BOTH_PHASES", result["reasons"])
        rows = self.rows()
        for row in rows:
            row.pop("synthetic_fixture")
        rows[3]["row_id"] = rows[2]["row_id"]
        result = mat_spec_006.check_future_split_structure(rows)
        self.assertIn("DUPLICATE_ROW_ID", result["reasons"])


class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = mat_spec_006.build_evidence(ROOT)
        cls.manifest = json.loads(cls.bundle["manifest.json"])

    def test_byte_replay_and_parent_lineage(self) -> None:
        self.assertEqual(self.bundle, mat_spec_006.build_evidence(ROOT))
        self.assertEqual(set(self.bundle), mat_spec_006.OUTPUT_NAMES)
        parent = mat_spec_005.build_evidence(ROOT)
        self.assertEqual(set(parent), set(self.manifest["parent"]["artifacts"]))
        self.assertEqual(
            {name: mat_spec.sha256(data) for name, data in parent.items()},
            mat_spec_006.PARENT_V5_SHA256,
        )
        for name, record in self.manifest["outputs"].items():
            self.assertEqual(mat_spec.sha256(self.bundle[name]), record["sha256"])
        for name, record in self.manifest["parent"]["artifacts"].items():
            self.assertEqual(mat_spec.sha256(parent[name]), record["sha256"])
        self.assertEqual(self.manifest["source"]["sha256"], mat_spec_006.SOURCE_SHA256)
        self.assertIsNone(self.manifest["canonical_pcm_sha256"])

    def test_no_physical_holdout_or_fake_uncertainty(self) -> None:
        actual = json.loads(self.bundle["phase-gate.json"])
        holdout = json.loads(self.bundle["heldout.json"])
        self.assertEqual(actual["primary_corrected_measurement_excerpts"], "REPLAY_VERIFIED")
        self.assertEqual(actual["independent_experimental_phase_validation"], "BLOCKED")
        self.assertEqual(actual["experiment_campaigns_with_admitted_numeric_rows"], 1)
        self.assertEqual(actual["independent_diagnostic_phase_labels"], 0)
        self.assertEqual(actual["positive_per_row_measured_uncertainties"], 0)
        self.assertFalse(actual["phase_classifier_trained"])
        self.assertIsNone(actual["phase_holdout_accuracy"])
        self.assertEqual(
            holdout["split_unit"], "distinct experimentally independent campaigns, never rows"
        )
        self.assertIsNone(holdout["physical_phase_heldout_accuracy"])
        csv_rows = list(csv.DictReader(io.StringIO(
            self.bundle["receiver-controls.csv"].decode("ascii")
        )))
        self.assertEqual(len(csv_rows), 12)

    def test_metadata_parent_and_source_forgery_rejected(self) -> None:
        native = mat_spec.read_regular

        def changed(path: Path, limit: int = 1_048_576) -> bytes:
            raw = native(path, limit)
            if path.name == "mat-spec-006.v0.1.json":
                return raw.replace(b'"row_count": 12', b'"row_count": 11')
            return raw

        with (
            patch("materials.mat_spec_006.mat_spec.read_regular", side_effect=changed),
            self.assertRaisesRegex(ValueError, "contract or source catalogue drift"),
        ):
            mat_spec_006.build_evidence(ROOT)
        parent = mat_spec_005.build_evidence(ROOT)
        expanded = dict(parent)
        expanded["injected.csv"] = b"tamper"
        with (
            patch("materials.mat_spec_006.mat_spec_005.build_evidence", return_value=expanded),
            self.assertRaisesRegex(ValueError, "parent membership"),
        ):
            mat_spec_006.build_evidence(ROOT)
        inventory = json.loads(mat_spec.read_regular(ROOT / mat_spec_006.INVENTORY_PATH))
        observations = mat_spec_006.parse_measurements(
            mat_spec.read_regular(ROOT / mat_spec_006.DATA_PATH)
        )
        forgery = [dict(row) for row in observations]
        forgery[0]["row_uncertainty_J_per_mol_K"] = "0.01"
        with self.assertRaisesRegex(ValueError, "forged experimental witness"):
            mat_spec_006.phase_gate(forgery, inventory)
        forgery = [dict(row) for row in observations]
        forgery[0]["independent_phase_label"] = "HE_II"
        with self.assertRaisesRegex(ValueError, "forged experimental witness"):
            mat_spec_006.phase_gate(forgery, inventory)

        drift = dict(parent)
        drift["phase-gate.json"] = b"tamper"
        with (
            patch("materials.mat_spec_006.mat_spec_005.build_evidence", return_value=drift),
            self.assertRaises(ValueError),
        ):
            mat_spec_006.build_evidence(ROOT)

    def test_symbolic_exclusive_output_and_render_audio_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = mat_spec_006.write_evidence(root, "dist/new", self.bundle)
            self.assertEqual({p.name for p in out.iterdir()}, mat_spec_006.OUTPUT_NAMES)
            with self.assertRaises(FileExistsError):
                mat_spec_006.write_evidence(root, "dist/new", self.bundle)
            outside = root / "outside"
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                mat_spec_006.write_evidence(root, "link/escape", self.bundle)
            self.assertEqual(list(outside.iterdir()), [])
            for bad in ("", "..", "../bad", "/abs", "x//y", "x/../y"):
                with self.assertRaises(ValueError):
                    mat_spec_006.write_evidence(root, bad, self.bundle)
            with self.assertRaises(ValueError):
                mat_spec_006.write_evidence(root, "bad", {"audio.wav": b"foo"})
        for args in (["--render-audio"], ["--format", "wav"]):
            p = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_mat_spec_006.py"), *args],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(p.returncode, 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX only")
    def test_symlink_and_fifo_source_denied(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            (target / "bad").symlink_to(ROOT / mat_spec_006.DATA_PATH)
            with self.assertRaises(OSError):
                mat_spec.read_regular(target / "bad")
            os.mkfifo(target / "fifo")
            with self.assertRaises(ValueError):
                mat_spec.read_regular(target / "fifo")


if __name__ == "__main__":
    unittest.main()
