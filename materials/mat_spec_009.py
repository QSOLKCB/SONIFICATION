"""MAT-SPEC-009: preregistered-future protocol and synthetic gate stress.

SPDX-License-Identifier: MPL-2.0
Copyright (c) 2026 Trent Slade / QSOL-IMC.

No independent experimental holdout is available. All executable fixtures
are synthetic, explicitly denied physical admission, never scored as physics.
No sampled audio, PCM or waveform buffers in memory or persisted.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import stat
from contextlib import suppress
from pathlib import Path, PurePosixPath

from materials import mat_spec, mat_spec_008

PROFILE = "MAT-SPEC-009"
VERSION = "0.1.0"
PARENT_COMMIT = "b4247877dd471e2e9d4986c86bdc1f11b14e43f8"
FOUNDATIONAL_DOI = "10.5281/zenodo.24062652"
SPEC_PATH = "spec/mat-spec-009.v0.1.json"
IMPLEMENTATION_PATHS = (
    "materials/mat_spec_009.py", "scripts/build_mat_spec_009.py",
)
OUTPUT_NAMES = frozenset({
    "contract.json", "source-gate.json", "split-protocol.json",
    "synthetic-controls.csv", "receiver-gate.json", "audit.json",
    "manifest.json",
})
EXPECTED_SOURCE_STATUS = "BLOCKED_INSUFFICIENT_INDEPENDENT_MEASUREMENT_DATA"
CONTROL_IDS = (
    "SYNTHETIC_CANDIDATE_DENIED",
    "CROSS_CAMPAIGN_RUN_REUSE",
    "CAMPAIGN_SPLIT_LEAKAGE",
    "SOURCE_BYTES_REUSED",
    "TEMPERATURE_DERIVED_LABEL",
    "ZERO_MEASUREMENT_SIGMA",
    "ORTHOGONAL_DIAGNOSTIC_ABSENT",
    "DIAGNOSTIC_SOURCE_EQUALS_MEASUREMENT",
    "UNDECLARED_RECEIVER_SCALE",
    "MISSING_PROSPECTIVE_REGISTRATION",
    "MIXED_PHYSICAL_PRESSURE",
    "HOLDOUT_MISSING_PHASE",
    "DERIVED_FIT_AS_MEASUREMENT",
    "DOCUMENT_REUSED",
)
SHA256_RE = re.compile(r"[0-9a-f]{64}")
# Pin all eight released MAT-SPEC-008 outputs from merged-main CI
# before PR is promoted from draft to review.
PARENT_V8_SHA256: dict[str, str] | None = None


def source_gate(parent: dict[str, bytes]) -> dict:
    """Read the real, unchanged 008 negative admission, never invent a sample."""
    record = json.loads(parent["admission.json"])
    audit = json.loads(parent["measurement-audit.json"])
    if (
        record["status"] != EXPECTED_SOURCE_STATUS
        or record["independent_measurement_campaigns_with_source_pinned_rows"] != 1
        or record["independent_measurement_campaign_pair_count"] != 0
        or record["independently_verified_raw_acquisition_campaigns"] != 0
        or record["physical_phase_accuracy"] is not None
        or record["source_separated_heldout_accuracy"] is not None
        or record["trained_phase_classifier"] is not False
        or audit["available_row_level_calibrated_uncertainties"] != 0
        or audit["available_independent_phase_diagnostic_rows"] != 0
        or audit["original_source_pinned_processed_measurement_campaigns"] != 1
        or audit["source_pinned_processed_measurement_rows"] != 12
    ):
        raise ValueError("unexpected MAT-SPEC-008 independent evidence admission drift")
    return {
        "input_profile": "MAT-SPEC-008", "parent_status": record["status"],
        "source_pinned_processed_campaigns": 1,
        "source_pinned_processed_rows": 12,
        "independent_measurement_pairs": 0,
        "calibrated_uncertainty_rows": 0,
        "independent_diagnostic_rows": 0,
        "physical_evidence_admitted": False,
        "challenge_enabled_for_real_measurements": False,
        "source_gate_reason": "NO_INDEPENDENT_SOURCE_SEPARATED_MEASUREMENT_CORPUS",
    }


def _identifier(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= 100
        and re.fullmatch(r"[A-Z0-9_]+", value) is not None
    )


def _digest(value: object) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def check_future_challenge(records: object) -> dict:
    """Structural-only source-family split check, never empirical certification.

    Input identity, metadata and hashes are user assertions. They are NOT a
    verified original acquisition or independently audited preregistration.
    """
    if not isinstance(records, list) or not records or len(records) > 10000:
        return {
            "status": "BLOCKED",
            "reasons": ["EMPTY_OR_MALFORMED_CHALLENGE"],
            "physical_evidence_admitted": False,
            "independence_authenticated": False,
            "heldout_accuracy": None,
        }
    parent = mat_spec_008.validate_future_measurement_packet(records)
    reasons = set(parent["reasons"])
    split_by_campaign: dict[str, str] = {}
    campaigns_by_split: dict[str, set[str]] = {
        "TRAIN": set(), "HOLDOUT": set(),
    }
    labs_by_split: dict[str, set[str]] = {
        "TRAIN": set(), "HOLDOUT": set(),
    }
    phases_by_split: dict[str, set[str]] = {
        "TRAIN": set(), "HOLDOUT": set(),
    }
    seen_registration: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            reasons.add("MALFORMED_CANDIDATE_RECORD")
            continue
        role = record.get("study_role")
        if role not in ("TRAIN", "HOLDOUT"):
            reasons.add("UNDECLARED_TRAIN_HOLDOUT_ROLE")
            continue
        campaign, lab = record.get("campaign_id"), record.get("lab_family_id")
        if not _identifier(campaign) or not _identifier(lab):
            reasons.add("MISSING_EXPERIMENT_FAMILY_IDENTITY")
            continue
        if campaign in split_by_campaign and split_by_campaign[campaign] != role:
            reasons.add("CAMPAIGN_CROSSES_TRAIN_HOLDOUT")
        split_by_campaign[campaign] = role
        campaigns_by_split[role].add(campaign)
        labs_by_split[role].add(lab)
        phase = record.get("phase")
        if isinstance(phase, str) and phase in ("HE_I", "HE_II"):
            phases_by_split[role].add(phase)
        if (
            record.get("measurement_quantity") != "HEAT_CAPACITY"
            or record.get("measurement_unit") != "J_PER_MOL_K"
        ):
            reasons.add("INCOMMENSURATE_MEASUREMENT_UNITS")
        if record.get("pressure_condition") != "HE4_SVP":
            reasons.add("UNDECLARED_PRESSURE_CONDITION")
        if record.get("receiver_scale") != "5":
            reasons.add("UNDECLARED_RECEIVER_SCALE")
        if record.get("label_basis") != "ORTHOGONAL_DIAGNOSTIC":
            reasons.add("CIRCULAR_OR_MISSING_ORTHOGONAL_LABEL")
        diagnostic_hash = record.get("diagnostic_sha256")
        source_hash = record.get("source_sha256")
        if (
            not _digest(diagnostic_hash) or diagnostic_hash == source_hash
            or not _identifier(record.get("diagnostic_event_id"))
        ):
            reasons.add("INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED")
        receipt = record.get("pre_registration_sha256")
        if not _digest(receipt):
            reasons.add("MISSING_PROSPECTIVE_REGISTRATION_RECEIPT")
        else:
            seen_registration.add(receipt)
    if len(seen_registration) != 1:
        reasons.add("INCONSISTENT_PREREGISTRATION_RECEIPT")
    if not campaigns_by_split["TRAIN"] or not campaigns_by_split["HOLDOUT"]:
        reasons.add("BOTH_EXPERIMENT_SPLITS_REQUIRED")
    if (campaigns_by_split["TRAIN"] & campaigns_by_split["HOLDOUT"]
        or labs_by_split["TRAIN"] & labs_by_split["HOLDOUT"]):
        reasons.add("SOURCE_FAMILY_LEAKAGE_ACROSS_SPLITS")
    for role in ("TRAIN", "HOLDOUT"):
        if phases_by_split[role] != {"HE_I", "HE_II"}:
            reasons.add(role + "_REQUIRES_BOTH_PHASES")
    # The existing parent gate catches reused run IDs, documents and hashes.
    # Even a passing structural check cannot authenticate source independence.
    outcome = sorted(reasons)
    return {
        "status": "BLOCKED" if outcome else "STRUCTURAL_ONLY_UNAUTHENTICATED",
        "reasons": outcome,
        "train_campaigns": len(campaigns_by_split["TRAIN"]),
        "heldout_campaigns": len(campaigns_by_split["HOLDOUT"]),
        "physical_evidence_admitted": False,
        "independence_authenticated": False,
        "heldout_accuracy": None,
        "trained_classifier": False,
        "meaning": "Synthetic or self-declared metadata never establishes external physical validation",
    }


def _synthetic_controls() -> list[dict]:
    """Synthetic, in-memory-only metadata fixtures with no physical authority."""
    records = []
    for campaign, lab, run, digest, diag, role in (
        ("SYNTH_TRAIN", "SYNTH_LAB_A", "SYNTH_RUN_A", "a" * 64, "c" * 64, "TRAIN"),
        ("SYNTH_HELD", "SYNTH_LAB_B", "SYNTH_RUN_B", "b" * 64, "d" * 64, "HOLDOUT"),
    ):
        for phase in ("HE_I", "HE_II"):
            records.append({
                "row_id": campaign + "_" + phase,
                "campaign_id": campaign, "lab_family_id": lab,
                "original_run_id": run,
                "source_document_id": "DOC_" + campaign,
                "source_sha256": digest,
                "diagnostic_sha256": diag,
                "diagnostic_event_id": "DIAG_" + campaign + "_" + phase,
                "source_type": "ORIGINAL_EXPERIMENTAL_RECORD",
                "measurement_quantity": "HEAT_CAPACITY",
                "measurement_unit": "J_PER_MOL_K",
                "measurement_value": "12.34",
                "measurement_sigma": "0.01",
                "diagnostic_sigma": "0.02",
                "diagnostic_basis": "INDEPENDENT_NON_TEMPERATURE_DIAGNOSTIC",
                "label_basis": "ORTHOGONAL_DIAGNOSTIC",
                "phase": phase,
                "receiver_scale": "5",
                "pre_registration_sha256": "e" * 64,
                "pressure_condition": "HE4_SVP",
                "study_role": role,
                "synthetic_fixture": True,
            })
    return records


def negative_controls() -> list[dict]:
    """Execute negative controls, recording only expected/observed error IDs.

    Never expose synthetic rows as experimental measurements or score them.
    """
    controls = (
        ("SYNTHETIC_CANDIDATE_DENIED", "SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT"),
        ("CROSS_CAMPAIGN_RUN_REUSE", "REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS"),
        ("CAMPAIGN_SPLIT_LEAKAGE", "CAMPAIGN_CROSSES_TRAIN_HOLDOUT"),
        ("SOURCE_BYTES_REUSED", "REUSED_SOURCE_BYTES_ACROSS_CAMPAIGNS"),
        ("TEMPERATURE_DERIVED_LABEL", "CIRCULAR_OR_MISSING_PHASE_DIAGNOSTIC"),
        ("ZERO_MEASUREMENT_SIGMA", "MISSING_CALIBRATED_MEASUREMENT_UNCERTAINTY"),
        ("ORTHOGONAL_DIAGNOSTIC_ABSENT", "INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED"),
        ("DIAGNOSTIC_SOURCE_EQUALS_MEASUREMENT", "INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED"),
        ("UNDECLARED_RECEIVER_SCALE", "UNDECLARED_RECEIVER_SCALE"),
        ("MISSING_PROSPECTIVE_REGISTRATION", "MISSING_PROSPECTIVE_REGISTRATION_RECEIPT"),
        ("MIXED_PHYSICAL_PRESSURE", "UNDECLARED_PRESSURE_CONDITION"),
        ("HOLDOUT_MISSING_PHASE", "HOLDOUT_REQUIRES_BOTH_PHASES"),
        ("DERIVED_FIT_AS_MEASUREMENT", "DERIVED_FIT_OR_COMPILATION_IS_NOT_PRIMARY_DATA"),
        ("DOCUMENT_REUSED", "REUSED_ORIGINAL_DOCUMENT_ACROSS_CAMPAIGNS"),
    )
    if tuple(x[0] for x in controls) != CONTROL_IDS:
        raise ValueError("frozen negative control order mismatch")
    results = []
    for control_id, expected_reason in controls:
        rows = _synthetic_controls()
        if control_id == "CROSS_CAMPAIGN_RUN_REUSE":
            for row in rows[2:]:
                row["original_run_id"] = "SYNTH_RUN_A"
        elif control_id == "CAMPAIGN_SPLIT_LEAKAGE":
            rows[1]["study_role"] = "HOLDOUT"
        elif control_id == "SOURCE_BYTES_REUSED":
            for row in rows[2:]:
                row["source_sha256"] = "a" * 64
        elif control_id == "TEMPERATURE_DERIVED_LABEL":
            rows[0]["diagnostic_basis"] = "TEMPERATURE_THRESHOLD"
        elif control_id == "ZERO_MEASUREMENT_SIGMA":
            rows[0]["measurement_sigma"] = "0"
        elif control_id == "ORTHOGONAL_DIAGNOSTIC_ABSENT":
            rows[0]["diagnostic_sha256"] = None
        elif control_id == "DIAGNOSTIC_SOURCE_EQUALS_MEASUREMENT":
            rows[0]["diagnostic_sha256"] = "a" * 64
        elif control_id == "UNDECLARED_RECEIVER_SCALE":
            rows[0]["receiver_scale"] = "10"
        elif control_id == "MISSING_PROSPECTIVE_REGISTRATION":
            rows[0]["pre_registration_sha256"] = ""
        elif control_id == "MIXED_PHYSICAL_PRESSURE":
            rows[0]["pressure_condition"] = "DOCUMENTED_FIXED_PRESSURE"
        elif control_id == "HOLDOUT_MISSING_PHASE":
            rows[3]["phase"] = "HE_I"
            rows[3]["row_id"] = "SYNTH_HELD_SECOND_HE_I"
        elif control_id == "DERIVED_FIT_AS_MEASUREMENT":
            rows[0]["source_type"] = "REANALYSIS"
        elif control_id == "DOCUMENT_REUSED":
            for row in rows[2:]:
                row["source_document_id"] = "DOC_SYNTH_TRAIN"
        outcome = check_future_challenge(rows)
        if (
            outcome["status"] != "BLOCKED"
            or expected_reason not in outcome["reasons"]
            or "SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT" not in outcome["reasons"]
            or outcome["physical_evidence_admitted"] is not False
            or outcome["heldout_accuracy"] is not None
        ):
            raise ValueError("synthetic negative control failed: " + control_id)
        results.append({
            "control_id": control_id,
            "synthetic_only": "true",
            "expected_rejection": expected_reason,
            "observed_rejection": expected_reason,
            "result": "PASS_REJECTED",
            "physical_evidence_admitted": "false",
            "classifier_accuracy": "NULL",
        })
    return results


def _csv(rows: list[dict]) -> bytes:
    if not rows:
        raise ValueError("empty result table")
    buff = io.StringIO(newline="")
    writer = csv.DictWriter(
        buff, fieldnames=list(rows[0]), lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return buff.getvalue().encode("ascii")


def build_evidence(root: Path) -> dict[str, bytes]:
    """Rebuild original eight profiles and preserve their exact identities."""
    parent = mat_spec_008.build_evidence(root)
    if set(parent) != mat_spec_008.OUTPUT_NAMES:
        raise ValueError("MAT-SPEC-008 parent membership mismatch")
    parents = {name: mat_spec.sha256(raw) for name, raw in parent.items()}
    if PARENT_V8_SHA256 is not None and parents != PARENT_V8_SHA256:
        raise ValueError("frozen MAT-SPEC-008 outputs drifted")
    prior = json.loads(parent["manifest.json"])
    if (
        prior.get("profile") != "MAT-SPEC-008"
        or prior.get("version") != "0.1.0"
        or prior.get("parent_commit") != mat_spec_008.PARENT_COMMIT
        or prior.get("foundational_mat_spec_001_doi") != FOUNDATIONAL_DOI
    ):
        raise ValueError("MAT-SPEC-008 ancestor identity mismatch")
    if set(prior["outputs"]) != set(parent) - {"manifest.json"} or any(
        mat_spec.sha256(parent[name]) != record["sha256"]
        for name, record in prior["outputs"].items()
    ):
        raise ValueError("ancestor output manifest inconsistency")
    source = source_gate(parent)
    spec_raw = mat_spec.read_regular(root / SPEC_PATH)
    try:
        contract = json.loads(spec_raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("MAT-SPEC-009 contract malformed") from exc
    if contract != EXPECTED_SPEC:
        raise ValueError("MAT-SPEC-009 prospective protocol drift")
    controls = negative_controls()
    if len(controls) != len(CONTROL_IDS):
        raise ValueError("synthetic control membership drift")
    split = {
        "profile": PROFILE, "version": VERSION,
        "status": "BLOCKED_NO_ADMITTED_SOURCE_SEPARATED_PHYSICAL_EVIDENCE",
        "source_gate": source["parent_status"],
        "split_unit": "original independent acquisition campaign",
        "prospective_protocol": True,
        "retrospectively_preregistered_for_mat_spec_006_008": False,
        "training_campaigns": 0, "heldout_campaigns": 0,
        "physical_records_assigned": 0,
        "synthetic_rows_admitted_as_physics": 0,
        "classifier_trained": False, "holdout_accuracy": None,
        "physical_evidence_admitted": False,
        "evaluation_performed": "SYNTHETIC_NEGATIVE_CONTROLS_ONLY",
    }
    receiver = {
        "status": "UNEXECUTED_FOR_PHYSICAL_CLASSIFICATION",
        "authored_scale": "5 Hz per J/(mol K)",
        "exact_source_math": "Fraction",
        "receiver": "nearest 12-TET note, symbolic only",
        "receiver_scale_tuned_on_holdout": False,
        "physical_performance": None,
        "quantized_source_separated_accuracy": None,
        "sampled_audio_generated": False,
    }
    audit = {
        "profile": PROFILE, "version": VERSION,
        "synthetic_negative_controls_executed": len(controls),
        "synthetic_negative_controls_passed": len(controls),
        "source_pinned_measurement_campaigns": 1,
        "eligible_independent_campaign_pairs": 0,
        "physical_validation_experiments_performed": 0,
        "phase_classifier_accuracy": None,
        "synthetic_accuracy_reported_as_physics": False,
        "program_stop": "MAT-SPEC-010",
    }
    outputs = {
        "contract.json": mat_spec.canonical_json(contract),
        "source-gate.json": mat_spec.canonical_json(source),
        "split-protocol.json": mat_spec.canonical_json(split),
        "synthetic-controls.csv": _csv(controls),
        "receiver-gate.json": mat_spec.canonical_json(receiver),
        "audit.json": mat_spec.canonical_json(audit),
    }
    impl = {
        path: mat_spec.sha256(mat_spec.read_regular(root / path))
        for path in IMPLEMENTATION_PATHS
    }
    manifest = {
        "profile": PROFILE, "version": VERSION,
        "parent_commit": PARENT_COMMIT,
        "parent_artifacts": {
            name: {"sha256": digest, "bytes": len(parent[name])}
            for name, digest in sorted(parents.items())
        },
        "contract": {"path": SPEC_PATH, "sha256": mat_spec.sha256(spec_raw)},
        "implementation": impl,
        "outputs": {
            name: {"sha256": mat_spec.sha256(data), "bytes": len(data)}
            for name, data in sorted(outputs.items())
        },
        "foundational_mat_spec_001_doi": FOUNDATIONAL_DOI,
        "canonical": "ASCII sorted compact JSON LF and CSV LF, no clock",
        "manifest_self_hash": None,
        "canonical_pcm_sha256": None,
        "canonical_wav_sha256": None,
        "audio_generated": False,
    }
    outputs["manifest.json"] = mat_spec.canonical_json(manifest)
    return outputs


def write_evidence(root: Path, destination: str, products: dict[str, bytes]) -> Path:
    """POSIX no-follow exclusive directory export, JSON/CSV only."""
    path = PurePosixPath(destination)
    if (
        not destination or path.is_absolute() or "\\" in destination
        or any(piece in {"", ".", ".."} for piece in destination.split("/"))
    ):
        raise ValueError("output must be a fresh relative directory")
    if set(products) != OUTPUT_NAMES or any(
        PurePosixPath(name).name != name
        or Path(name).suffix not in {".csv", ".json"} for name in products
    ):
        raise ValueError("non-symbolic runtime output is forbidden")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fds = [os.open(root, flags)]
    try:
        for part in path.parts[:-1]:
            with suppress(FileExistsError):
                os.mkdir(part, mode=0o755, dir_fd=fds[-1])
            fds.append(os.open(part, flags, dir_fd=fds[-1]))
        parent_fd = fds[-1]
        os.mkdir(path.parts[-1], mode=0o755, dir_fd=parent_fd)
        fds.append(os.open(path.parts[-1], flags, dir_fd=parent_fd))
        out = fds[-1]
        for name in sorted(products):
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode=0o644, dir_fd=out,
            )
            with os.fdopen(fd, "wb") as target:
                target.write(products[name])
        opened = os.fstat(out)
        visible = os.stat(path.parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISDIR(visible.st_mode) or (
            opened.st_dev, opened.st_ino
        ) != (visible.st_dev, visible.st_ino):
            raise ValueError("output directory changed during export")
    finally:
        for fd in reversed(fds):
            os.close(fd)
    return root / path

EXPECTED_SPEC = json.loads(
    "{\"profile\":\"MAT-SPEC-009\",\"version\":\"0.1.0\",\"parent_profile\""
    ":\"MAT-SPEC-008 v0.1.0\",\"parent_merge_commit\":\"b4247877dd471e"
    "2e9d4986c86bdc1f11b14e43f8\",\"foundational_mat_spec_001_doi\":"
    "\"10.5281/zenodo.24062652\",\"research_question\":\"Can a frozen "
    "symbolic receiver preserve independently measured helium-I a"
    "nd helium-II phase evidence on a source-separated experiment"
    " holdout?\",\"protocol_status\":\"PROSPECTIVE_FOR_FUTURE_ACQUISI"
    "TIONS_ONLY\",\"timing\":\"Document frozen after examining MAT-SP"
    "EC-001 through MAT-SPEC-008 data; not a retrospective prereg"
    "istration for prior experiments\",\"predecessor_gate_required\""
    ":\"INDEPENDENT_MEASUREMENTS_ADMITTED\",\"source_separation_unit"
    "\":\"original independent acquisition campaign; never split re"
    "cords within a campaign\",\"partition\":\"explicit TRAIN or HOLD"
    "OUT; two families, one campaign minimum in each; both phases"
    " per partition\",\"admissible_observable\":\"HE4_SVP heat_capaci"
    "ty J_PER_MOL_K; positive calibrated per-row uncertainties; i"
    "ndependent non-temperature phase diagnostics with distinct s"
    "ource SHA\",\"receiver\":\"Fraction-preserving authored symbolic"
    " 5 Hz per J/(mol K), quantize only after exact mapping; scal"
    "e fixed before training and never tuned on holdout\",\"metrics"
    "\":\"reserved: predeclared source-family-separated confusion m"
    "atrix and discrimination with uncertainty, only after physic"
    "al admission; no scores in this release\",\"nonclaims\":\"NO_REA"
    "L_PHASE_CLASSIFIER_NO_INDEPENDENT_HOLDOUT_NO_EXPERIMENTAL_AC"
    "CURACY_NO_LISTENER_RESULT\",\"synthetic_policy\":\"negative cont"
    "rols only; all synthetic fixtures are explicitly rejected as"
    " physical data, never included as empirical accuracy\",\"prosp"
    "ective_registration\":\"future external registered receipt mus"
    "t be independently verified, a candidate SHA alone never cer"
    "tifies preregistration\",\"output_policy\":\"canonical ASCII JSO"
    "N and CSV; no sampled waveform PCM WAV or playback\",\"program"
    "_stop\":\"MAT-SPEC-010 is final; SPARK/Ada and VANILLAJS Lean-"
    "ECMA afterwards\"}"
)
