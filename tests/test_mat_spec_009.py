"""MAT-SPEC-009: source-separated preflight and synthetic negative controls.

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
from pathlib import Path
from unittest.mock import patch

from materials import mat_spec, mat_spec_008, mat_spec_009

ROOT = Path(__file__).resolve().parents[1]


class ChallengeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = mat_spec_009._synthetic_controls()

    def test_synthetic_controls_never_admitted_as_physics(self) -> None:
        decision = mat_spec_009.check_future_challenge(self.rows)
        self.assertEqual(decision["status"], "BLOCKED")
        self.assertEqual(
            decision["reasons"],
            ["SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT"],
        )
        self.assertFalse(decision["physical_evidence_admitted"])
        self.assertFalse(decision["independence_authenticated"])
        self.assertIsNone(decision["heldout_accuracy"])
        self.assertFalse(decision["trained_classifier"])

    def test_self_declared_healthy_metadata_is_still_unverified(self) -> None:
        for row in self.rows:
            del row["synthetic_fixture"]
        decision = mat_spec_009.check_future_challenge(self.rows)
        self.assertEqual(decision["status"], "STRUCTURAL_ONLY_UNAUTHENTICATED")
        self.assertEqual(decision["reasons"], [])
        self.assertEqual(decision["train_campaigns"], 1)
        self.assertEqual(decision["heldout_campaigns"], 1)
        self.assertFalse(decision["physical_evidence_admitted"])
        self.assertFalse(decision["independence_authenticated"])
        self.assertIsNone(decision["heldout_accuracy"])
        self.assertEqual(
            mat_spec_008.validate_future_measurement_packet(self.rows)["status"],
            "STRUCTURAL_ONLY_UNAUTHENTICATED",
        )

    def test_immutable_fourteen_negative_controls_execute(self) -> None:
        results = mat_spec_009.negative_controls()
        self.assertEqual(len(results), 14)
        self.assertEqual(
            tuple(row["control_id"] for row in results),
            mat_spec_009.CONTROL_IDS,
        )
        self.assertTrue(all(row["synthetic_only"] == "true" for row in results))
        self.assertTrue(all(row["result"] == "PASS_REJECTED" for row in results))
        self.assertTrue(all(row["classifier_accuracy"] == "NULL" for row in results))
        self.assertEqual(results, mat_spec_009.negative_controls())

    def test_campaign_and_lab_train_holdout_isolation(self) -> None:
        self.rows[1]["study_role"] = "HOLDOUT"
        decision = mat_spec_009.check_future_challenge(self.rows)
        self.assertIn("CAMPAIGN_CROSSES_TRAIN_HOLDOUT", decision["reasons"])
        self.assertIn("SOURCE_FAMILY_LEAKAGE_ACROSS_SPLITS", decision["reasons"])
        self.assertEqual(decision["status"], "BLOCKED")

    def test_receiver_units_and_pressure_are_declared_before_split(self) -> None:
        cases = (
            ("measurement_unit", "M_PER_S", "INCOMMENSURATE_MEASUREMENT_UNITS"),
            ("measurement_quantity", "SOUND_SPEED", "INCOMMENSURATE_MEASUREMENT_UNITS"),
            ("receiver_scale", "10", "UNDECLARED_RECEIVER_SCALE"),
            ("receiver_scale", "5.0", "UNDECLARED_RECEIVER_SCALE"),
            ("pressure_condition", "DOCUMENTED_FIXED_PRESSURE",
             "UNDECLARED_PRESSURE_CONDITION"),
            ("label_basis", "TEMPERATURE_THRESHOLD",
             "CIRCULAR_OR_MISSING_ORTHOGONAL_LABEL"),
            ("diagnostic_sha256", "a" * 64, "INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED"),
            ("pre_registration_sha256", "", "MISSING_PROSPECTIVE_REGISTRATION_RECEIPT"),
        )
        for key, value, code in cases:
            with self.subTest(key=key, value=value):
                records = mat_spec_009._synthetic_controls()
                records[0][key] = value
                result = mat_spec_009.check_future_challenge(records)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertIn(code, result["reasons"])
                self.assertIsNone(result["heldout_accuracy"])

    def test_both_phases_required_in_each_group(self) -> None:
        self.rows[3]["phase"] = "HE_I"
        self.rows[3]["row_id"] = "SYNTH_HELD_OTHER_I"
        outcome = mat_spec_009.check_future_challenge(self.rows)
        self.assertIn("HOLDOUT_REQUIRES_BOTH_PHASES", outcome["reasons"])
        self.assertIn(
            "BOTH_PHASES_REQUIRED_FOR_EACH_CAMPAIGN", outcome["reasons"]
        )

    def test_parent_rejects_cross_campaign_reused_original_run_and_bytes(self) -> None:
        cases = (
            ("original_run_id", "SYNTH_RUN_A", "REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS"),
            ("source_document_id", "DOC_SYNTH_TRAIN",
             "REUSED_ORIGINAL_DOCUMENT_ACROSS_CAMPAIGNS"),
            ("source_sha256", "a" * 64, "REUSED_SOURCE_BYTES_ACROSS_CAMPAIGNS"),
        )
        for key, value, code in cases:
            with self.subTest(field=key):
                records = mat_spec_009._synthetic_controls()
                for row in records[2:]:
                    row[key] = value
                outcome = mat_spec_009.check_future_challenge(records)
                self.assertIn(code, outcome["reasons"])
                self.assertFalse(outcome["physical_evidence_admitted"])

    def test_blank_nonstring_and_missing_preregistration_fail(self) -> None:
        for bad in ("", "  ", None, {}, ["bad"]):
            with self.subTest(bad=bad):
                records = mat_spec_009._synthetic_controls()
                records[0]["pre_registration_sha256"] = bad
                result = mat_spec_009.check_future_challenge(records)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertIn(
                    "MISSING_PROSPECTIVE_REGISTRATION_RECEIPT", result["reasons"]
                )
        self.assertIn(
            "EMPTY_OR_MALFORMED_CHALLENGE",
            mat_spec_009.check_future_challenge([])["reasons"],
        )
        self.assertEqual(
            mat_spec_009.check_future_challenge({})["status"], "BLOCKED"
        )
        self.assertEqual(
            mat_spec_009.check_future_challenge([None])["status"], "BLOCKED"
        )
        self.assertEqual(
            mat_spec_009.check_future_challenge([{}] * 10001)["status"],
            "BLOCKED",
        )

    def test_pretended_pre_registration_receipt_does_not_admit(self) -> None:
        records = mat_spec_009._synthetic_controls()
        for row in records:
            del row["synthetic_fixture"]
        records[0]["pre_registration_sha256"] = "f" * 64
        result = mat_spec_009.check_future_challenge(records)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("INCONSISTENT_PREREGISTRATION_RECEIPT", result["reasons"])
        self.assertFalse(result["independence_authenticated"])

    def test_distinct_reviewer_gate_is_not_physical_admission(self) -> None:
        parent = mat_spec_008.build_evidence(ROOT)
        source = mat_spec_009.source_gate(parent)
        self.assertEqual(
            source["parent_status"],
            "BLOCKED_INSUFFICIENT_INDEPENDENT_MEASUREMENT_DATA",
        )
        self.assertEqual(source["source_pinned_processed_campaigns"], 1)
        self.assertEqual(source["source_pinned_processed_rows"], 12)
        self.assertEqual(source["independent_measurement_pairs"], 0)
        self.assertFalse(source["challenge_enabled_for_real_measurements"])
        forged = dict(parent)
        admission = json.loads(parent["admission.json"])
        admission["source_separated_heldout_accuracy"] = "1.0"
        forged["admission.json"] = mat_spec.canonical_json(admission)
        with self.assertRaisesRegex(ValueError, "admission drift"):
            mat_spec_009.source_gate(forged)


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.outputs = mat_spec_009.build_evidence(ROOT)
        cls.manifest = json.loads(cls.outputs["manifest.json"])

    def test_rebuild_byte_determinism_and_hash_manifests(self) -> None:
        self.assertEqual(self.outputs, mat_spec_009.build_evidence(ROOT))
        self.assertEqual(set(self.outputs), mat_spec_009.OUTPUT_NAMES)
        ancestor = mat_spec_008.build_evidence(ROOT)
        self.assertEqual(set(ancestor), set(self.manifest["parent_artifacts"]))
        for name, record in self.manifest["parent_artifacts"].items():
            self.assertEqual(mat_spec.sha256(ancestor[name]), record["sha256"])
        for name, record in self.manifest["outputs"].items():
            self.assertEqual(mat_spec.sha256(self.outputs[name]), record["sha256"])
        self.assertIsNone(self.manifest["canonical_pcm_sha256"])
        self.assertIsNone(self.manifest["canonical_wav_sha256"])
        self.assertFalse(self.manifest["audio_generated"])

    def test_no_real_classifier_and_no_synthetic_empirical_accuracy(self) -> None:
        protocol = json.loads(self.outputs["split-protocol.json"])
        receiver = json.loads(self.outputs["receiver-gate.json"])
        source = json.loads(self.outputs["source-gate.json"])
        audit = json.loads(self.outputs["audit.json"])
        self.assertEqual(protocol["training_campaigns"], 0)
        self.assertEqual(protocol["heldout_campaigns"], 0)
        self.assertEqual(protocol["physical_records_assigned"], 0)
        self.assertIsNone(protocol["holdout_accuracy"])
        self.assertFalse(protocol["classifier_trained"])
        self.assertEqual(
            protocol["evaluation_performed"], "SYNTHETIC_NEGATIVE_CONTROLS_ONLY"
        )
        self.assertEqual(
            receiver["status"], "UNEXECUTED_FOR_PHYSICAL_CLASSIFICATION"
        )
        self.assertFalse(receiver["sampled_audio_generated"])
        self.assertEqual(source["independent_measurement_pairs"], 0)
        self.assertEqual(audit["synthetic_negative_controls_executed"], 14)
        self.assertEqual(audit["synthetic_negative_controls_passed"], 14)
        self.assertIsNone(audit["phase_classifier_accuracy"])
        rows = list(csv.DictReader(io.StringIO(
            self.outputs["synthetic-controls.csv"].decode("ascii")
        )))
        self.assertEqual(len(rows), 14)
        self.assertTrue(all(r["physical_evidence_admitted"] == "false" for r in rows))
        self.assertTrue(all(r["classifier_accuracy"] == "NULL" for r in rows))

    def test_parent_mutation_contract_drift_and_extra_file_fail(self) -> None:
        prev = mat_spec_008.build_evidence(ROOT)
        injected = dict(prev)
        injected["unexpected.csv"] = b"fake"
        with (
            patch("materials.mat_spec_009.mat_spec_008.build_evidence",
                  return_value=injected),
            self.assertRaisesRegex(ValueError, "membership"),
        ):
            mat_spec_009.build_evidence(ROOT)
        changed = dict(prev)
        changed["admission.json"] = b"corrupt"
        with (
            patch("materials.mat_spec_009.mat_spec_008.build_evidence",
                  return_value=changed),
            self.assertRaises(ValueError),
        ):
            mat_spec_009.build_evidence(ROOT)
        native = mat_spec.read_regular

        def mutated(path: Path, limit: int = 1_048_576) -> bytes:
            raw = native(path, limit)
            if path.name == "mat-spec-009.v0.1.json":
                return raw.replace(b'"version": "0.1.0"', b'"version": "0.2.0"')
            return raw

        with (
            patch("materials.mat_spec_009.mat_spec.read_regular", side_effect=mutated),
            self.assertRaisesRegex(ValueError, "protocol drift"),
        ):
            mat_spec_009.build_evidence(ROOT)

    def test_exclusive_relative_output_and_no_root_audio(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = mat_spec_009.write_evidence(root, "dist/out", self.outputs)
            self.assertEqual(set(p.name for p in out.iterdir()), mat_spec_009.OUTPUT_NAMES)
            with self.assertRaises(FileExistsError):
                mat_spec_009.write_evidence(root, "dist/out", self.outputs)
            outside = root / "outside"
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                mat_spec_009.write_evidence(root, "link/escape", self.outputs)
            self.assertEqual(list(outside.iterdir()), [])
            for bad in ("", "..", "../bad", "/absolute", "a//b", "a/../b"):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    mat_spec_009.write_evidence(root, bad, self.outputs)
            with self.assertRaises(ValueError):
                mat_spec_009.write_evidence(root, "bad", {"wave.wav": b"not permitted"})
        for flags in (["--render-audio"], ["--format", "wav"]):
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_mat_spec_009.py"), *flags],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX-specific special file")
    def test_symlink_and_fifo_input_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "symlink").symlink_to(ROOT / mat_spec_009.SPEC_PATH)
            with self.assertRaises(OSError):
                mat_spec.read_regular(root / "symlink")
            os.mkfifo(root / "fifo")
            with self.assertRaises(ValueError):
                mat_spec.read_regular(root / "fifo")


if __name__ == "__main__":
    unittest.main()
