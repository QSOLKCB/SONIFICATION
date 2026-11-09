"""MAT-SPEC-008: source lineage, admission, replay and negative controls.

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

from materials import mat_spec, mat_spec_006, mat_spec_007, mat_spec_008

ROOT = Path(__file__).resolve().parents[1]


def packet_fixture(
    campaign: str, family: str, run: str, phase: str
) -> dict:
    return {
        "campaign_id": campaign,
        "lab_family_id": family,
        "original_run_id": run,
        "source_document_id": "DOC_" + campaign,
        "row_id": campaign + "_" + phase,
        "source_type": "ORIGINAL_EXPERIMENTAL_RECORD",
        "measurement_value": "12.34",
        "measurement_sigma": "0.01",
        "diagnostic_sigma": "0.02",
        "diagnostic_basis": "INDEPENDENT_NON_TEMPERATURE_DIAGNOSTIC",
        "phase": phase,
        "source_sha256": ("a" if campaign == "CAMPAIGN_ONE" else "b") * 64,
        "pressure_condition": "HE4_SVP",
    }


def two_campaign_fixture() -> list[dict]:
    return [
        packet_fixture("CAMPAIGN_ONE", "LAB_A", "RUN_01", "HE_I"),
        packet_fixture("CAMPAIGN_ONE", "LAB_A", "RUN_01", "HE_II"),
        packet_fixture("CAMPAIGN_TWO", "LAB_B", "RUN_02", "HE_I"),
        packet_fixture("CAMPAIGN_TWO", "LAB_B", "RUN_02", "HE_II"),
    ]


class SourceAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = mat_spec.read_regular(ROOT / mat_spec_008.SOURCE_PATH)
        cls.catalogue = mat_spec_008.parse_catalogue(cls.source)
        assert mat_spec.sha256(cls.source) == mat_spec_008.CATALOGUE_SHA256
        cls.original = mat_spec_006.parse_measurements(
            mat_spec.read_regular(ROOT / mat_spec_006.DATA_PATH)
        )
        cls.fits = mat_spec_007.parse_source(
            mat_spec.read_regular(ROOT / mat_spec_007.SOURCE_PATH)
        )
        cls.campaigns, cls.pairs, cls.report = mat_spec_008.source_audit(
            cls.catalogue, cls.original, cls.fits
        )

    def test_catalogue_preserves_original_vs_reanalysis(self) -> None:
        docs = self.catalogue["source_docs"]
        self.assertEqual(len(docs), 10)
        self.assertEqual(tuple(d["doc_id"] for d in docs), mat_spec_008.DOC_IDS)
        self.assertEqual(sum(d["source_bound_measurement_rows"] for d in docs), 12)
        self.assertEqual(
            len({d["campaign"] for d in docs if d["campaign"] is not None}), 4
        )
        ground = next(d for d in docs if d["doc_id"] == "LC83_NASA_1984")
        self.assertEqual(ground["source_bound_measurement_rows"], 12)
        self.assertEqual(ground["campaign"], "LC83_SVP")
        refit = next(d for d in docs if d["doc_id"] == "GASPARINI_GAETA_PRB_1978")
        self.assertEqual(refit["document_kind"], "REANALYSIS")
        self.assertEqual(refit["campaign"], "GM75_SVP")
        orb = [
            d for d in docs if d["campaign"] == "STS52_1992"
        ]
        self.assertEqual(len(orb), 3)
        self.assertEqual({d["source_bound_measurement_rows"] for d in orb}, {0})
        self.assertTrue(all(not d["orthogonal_phase_diagnostic"] for d in docs))

    def test_experiment_campaign_pairs_are_not_admitted_as_raw_replications(
        self,
    ) -> None:
        self.assertEqual(len(self.pairs), 6)
        self.assertEqual(
            [row["campaign"] for row in self.campaigns],
            list(mat_spec_008.CAMPAIGNS),
        )
        self.assertEqual(
            [row["source_pinned_processed_measurement_rows"] for row in self.campaigns],
            [0, 0, 12, 0],
        )
        self.assertEqual(self.report["distinct_lab_families"], 3)
        self.assertEqual(self.report["reviewed_publication_documents"], 10)
        self.assertEqual(self.report["candidate_cross_lab_pairs"], 5)
        self.assertEqual(self.report["measurement_level_replicable_pairs"], 0)
        self.assertEqual(self.report["secondary_review_fitted_records"], 4)
        self.assertEqual(len(self.original), 12)
        self.assertTrue(all(
            not p["eligible_for_independent_replication"] for p in self.pairs
        ))

    def test_original_and_review_provenance_cannot_be_silently_joined(self) -> None:
        modified = [dict(row) for row in self.original]
        modified[0]["independent_phase_label"] = "HE_II"
        with self.assertRaisesRegex(ValueError, "forged"):
            mat_spec_008.source_audit(self.catalogue, modified, self.fits)
        altered_fit = [dict(row) for row in self.fits]
        altered_fit[0]["acquisition_campaign"] = "MUELLER_1976_AS_NEW"
        with self.assertRaisesRegex(ValueError, "lineage drift"):
            mat_spec_008.source_audit(self.catalogue, self.original, altered_fit)
        modified_catalogue = dict(self.catalogue)
        modified_catalogue["source_docs"] = [
            dict(entry) for entry in self.catalogue["source_docs"]
        ]
        modified_catalogue["source_docs"][1]["source_bound_measurement_rows"] = 20
        with self.assertRaisesRegex(ValueError, "unsupported independent"):
            mat_spec_008.source_audit(modified_catalogue, self.original, self.fits)

    def test_catalogue_byte_tamper_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHA-256|catalogue mismatch"):
            mat_spec_008.parse_catalogue(
                self.source.replace(b'"MAT-SPEC-008"', b'"MAT-SPEC-080"')
            )
        with self.assertRaises(ValueError):
            mat_spec_008._identity("")
        with self.assertRaises(ValueError):
            mat_spec_008._identity("  ")
        with self.assertRaises(ValueError):
            mat_spec_008._identity(None)
        with self.assertRaises(ValueError):
            mat_spec_008._identity(" PADDED ")

    def test_real_admission_fails_closed_without_classifier_score(self) -> None:
        result = mat_spec_008.evidence_admission(self.report, self.catalogue)
        self.assertEqual(
            result["status"], "BLOCKED_INSUFFICIENT_INDEPENDENT_MEASUREMENT_DATA"
        )
        self.assertEqual(
            result["independent_measurement_campaigns_with_source_pinned_rows"], 1
        )
        self.assertIsNone(result["physical_phase_accuracy"])
        self.assertIsNone(result["source_separated_heldout_accuracy"])
        self.assertFalse(result["trained_phase_classifier"])
        self.assertEqual(
            result["independent_measurement_campaign_pair_count"], 0
        )


class FuturePacketTests(unittest.TestCase):
    def test_structurally_complete_records_do_not_authenticate_independence(self) -> None:
        result = mat_spec_008.validate_future_measurement_packet(
            two_campaign_fixture()
        )
        self.assertEqual(result["status"], "STRUCTURAL_ONLY_UNAUTHENTICATED")
        self.assertEqual(result["described_campaigns"], 2)
        self.assertFalse(result["physical_evidence_admitted"])
        self.assertFalse(result["independence_authenticated"])
        self.assertIsNone(result["heldout_accuracy"])

    def test_synthetic_or_derived_source_rejected(self) -> None:
        for field, value, reason in (
            ("synthetic_fixture", True, "SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT"),
            ("source_type", "REANALYSIS", "DERIVED_FIT_OR_COMPILATION_IS_NOT_PRIMARY_DATA"),
            ("diagnostic_basis", "TEMPERATURE_THRESHOLD", "CIRCULAR_OR_MISSING_PHASE_DIAGNOSTIC"),
            ("measurement_sigma", "0", "MISSING_CALIBRATED_MEASUREMENT_UNCERTAINTY"),
            ("measurement_value", "NaN", "MISSING_CALIBRATED_MEASUREMENT_UNCERTAINTY"),
            ("source_sha256", "invalid", "SOURCE_HASH_OR_PHYSICAL_CONDITION_NOT_DOCUMENTED"),
        ):
            with self.subTest(field=field):
                rows = two_campaign_fixture()
                rows[0][field] = value
                result = mat_spec_008.validate_future_measurement_packet(rows)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertIn(reason, result["reasons"])

    def test_original_source_identity_and_phase_coverage_cannot_be_reused(
        self,
    ) -> None:
        for field, value, reason in (
            ("original_run_id", "RUN_01", "REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS"),
            (
                "source_document_id", "DOC_CAMPAIGN_ONE",
                "REUSED_ORIGINAL_DOCUMENT_ACROSS_CAMPAIGNS",
            ),
            ("source_sha256", "a" * 64, "REUSED_SOURCE_BYTES_ACROSS_CAMPAIGNS"),
        ):
            with self.subTest(field=field):
                records = two_campaign_fixture()
                for item in records[2:]:
                    item[field] = value
                result = mat_spec_008.validate_future_measurement_packet(records)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertIn(reason, result["reasons"])
                self.assertFalse(result["physical_evidence_admitted"])
        records = two_campaign_fixture()
        records[3]["phase"] = "HE_I"
        result = mat_spec_008.validate_future_measurement_packet(records)
        self.assertIn("BOTH_PHASES_REQUIRED_FOR_EACH_CAMPAIGN", result["reasons"])

    def test_empty_padded_duplicate_and_reused_run_identifiers(self) -> None:
        for field, value in (
            ("campaign_id", ""), ("lab_family_id", "  "),
            ("source_document_id", " BAD "), ("original_run_id", None),
        ):
            with self.subTest(field=field):
                rows = two_campaign_fixture()
                rows[0][field] = value
                result = mat_spec_008.validate_future_measurement_packet(rows)
                self.assertIn(
                    "MISSING_OR_INVALID_SOURCE_IDENTITIES", result["reasons"]
                )
        rows = two_campaign_fixture()
        rows[3]["row_id"] = rows[2]["row_id"]
        self.assertIn(
            "DUPLICATE_MEASUREMENT_ROW_ID",
            mat_spec_008.validate_future_measurement_packet(rows)["reasons"],
        )
        rows = two_campaign_fixture()
        for row in rows[2:]:
            row["lab_family_id"] = "LAB_A"
        self.assertIn(
            "TWO_INDEPENDENT_CAMPAIGNS_AND_LABS_REQUIRED",
            mat_spec_008.validate_future_measurement_packet(rows)["reasons"],
        )
        rows = two_campaign_fixture()
        for row in rows[2:]:
            row["original_run_id"] = "RUN_01"
            row["source_document_id"] = "DOC_CAMPAIGN_ONE"
        self.assertIn(
            "DISTINCT_ORIGINAL_RUNS_REQUIRED",
            mat_spec_008.validate_future_measurement_packet(rows)["reasons"],
        )


class RuntimeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = mat_spec_008.build_evidence(ROOT)
        cls.manifest = json.loads(cls.bundle["manifest.json"])

    def test_bundle_replays_parent_and_manifest_hashes(self) -> None:
        self.assertEqual(self.bundle, mat_spec_008.build_evidence(ROOT))
        self.assertEqual(set(self.bundle), mat_spec_008.OUTPUT_NAMES)
        self.assertEqual(self.manifest["profile"], "MAT-SPEC-008")
        self.assertEqual(self.manifest["parent_commit"], mat_spec_008.PARENT_COMMIT)
        self.assertEqual(
            self.manifest["foundational_mat_spec_001_doi"],
            mat_spec_008.FOUNDATIONAL_DOI,
        )
        original = mat_spec_007.build_evidence(ROOT)
        self.assertEqual(set(original), set(self.manifest["parent_outputs"]))
        self.assertEqual(
            {name: mat_spec.sha256(raw) for name, raw in original.items()},
            mat_spec_008.PARENT_V7_SHA256,
        )
        self.assertEqual(
            self.manifest["source_catalogue"]["sha256"],
            mat_spec_008.CATALOGUE_SHA256,
        )
        for name, record in self.manifest["parent_outputs"].items():
            self.assertEqual(record["sha256"], mat_spec.sha256(original[name]))
        for name, record in self.manifest["outputs"].items():
            self.assertEqual(mat_spec.sha256(self.bundle[name]), record["sha256"])
        self.assertFalse(self.manifest["audio_generated"])
        self.assertIsNone(self.manifest["canonical_pcm_sha256"])

    def test_frozen_source_admission_and_six_pairs(self) -> None:
        admission = json.loads(self.bundle["admission.json"])
        self.assertEqual(admission["train_test_split"], "NOT_PERFORMED")
        self.assertEqual(admission["independent_measurement_campaign_pair_count"], 0)
        self.assertEqual(admission["program_end"], "MAT-SPEC-010")
        rows = list(csv.DictReader(io.StringIO(
            self.bundle["candidate-pairs.csv"].decode("ascii")
        )))
        self.assertEqual(len(rows), 6)
        campaigns = list(csv.DictReader(io.StringIO(
            self.bundle["campaigns.csv"].decode("ascii")
        )))
        self.assertEqual(len(campaigns), 4)
        self.assertEqual(len(json.loads(self.bundle["source-catalogue.json"])["source_docs"]), 10)

    def test_parent_mutation_contract_drift_and_extra_members_fail(self) -> None:
        native = mat_spec.read_regular

        def drifted(path: Path, limit: int = 1_048_576) -> bytes:
            raw = native(path, limit)
            if path.name == "mat-spec-008.v0.1.json":
                return raw.replace(b'"version": "0.1.0"', b'"version": "0.2.0"')
            return raw

        with (
            patch("materials.mat_spec_008.mat_spec.read_regular", side_effect=drifted),
            self.assertRaisesRegex(ValueError, "contract drift"),
        ):
            mat_spec_008.build_evidence(ROOT)
        prev = mat_spec_007.build_evidence(ROOT)
        extra = dict(prev)
        extra["injected.csv"] = b"fake"
        with (
            patch("materials.mat_spec_008.mat_spec_007.build_evidence", return_value=extra),
            self.assertRaisesRegex(ValueError, "membership"),
        ):
            mat_spec_008.build_evidence(ROOT)
        changed = dict(prev)
        changed["audit.json"] = b"not the frozen bytes"
        with (
            patch("materials.mat_spec_008.mat_spec_007.build_evidence", return_value=changed),
            self.assertRaises(ValueError),
        ):
            mat_spec_008.build_evidence(ROOT)

    def test_no_follow_output_and_audio_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = mat_spec_008.write_evidence(root, "dist/run", self.bundle)
            self.assertEqual({p.name for p in out.iterdir()}, mat_spec_008.OUTPUT_NAMES)
            with self.assertRaises(FileExistsError):
                mat_spec_008.write_evidence(root, "dist/run", self.bundle)
            elsewhere = root / "outside"
            elsewhere.mkdir()
            (root / "link").symlink_to(elsewhere, target_is_directory=True)
            with self.assertRaises(OSError):
                mat_spec_008.write_evidence(root, "link/escape", self.bundle)
            self.assertEqual(list(elsewhere.iterdir()), [])
            for invalid in ("", "..", "../x", "/absolute", "a//b", "x/../y"):
                with self.assertRaises(ValueError):
                    mat_spec_008.write_evidence(root, invalid, self.bundle)
            with self.assertRaises(ValueError):
                mat_spec_008.write_evidence(root, "wave", {"sound.wav": b"raw"})
        for args in (["--render-audio"], ["--format", "wav"]):
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_mat_spec_008.py"), *args],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX-only FIFO")
    def test_special_input_files_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "linked").symlink_to(ROOT / mat_spec_008.SOURCE_PATH)
            with self.assertRaises(OSError):
                mat_spec.read_regular(root / "linked")
            os.mkfifo(root / "fifo")
            with self.assertRaises(ValueError):
                mat_spec.read_regular(root / "fifo")


if __name__ == "__main__":
    unittest.main()
