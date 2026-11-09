"""MAT-SPEC-006: primary calorimetry evidence and source-separated phase preflight.

SPDX-License-Identifier: MPL-2.0
Copyright (c) 2026 Trent Slade / QSOL-IMC.

Primary measurements are gravity-corrected/averaged; no new independent
phase labels, measurement uncertainties, rendered audio or invented accuracy.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import stat
from contextlib import suppress
from fractions import Fraction
from itertools import combinations, pairwise
from pathlib import Path, PurePosixPath

from materials import mat_spec, mat_spec_005

PROFILE = "MAT-SPEC-006"
VERSION = "0.1.0"
PARENT_COMMIT = "5b4c89b795beb7fc8c4f7d86ce2a2fb510cb6cb2"
PARENT_DOI = "10.5281/zenodo.24062652"
DATA_PATH = "data/materials/helium4/lipa_chui_1984_excerpt.csv"
META_PATH = "data/materials/helium4/lipa_chui_1984.source.json"
INVENTORY_PATH = "data/materials/helium4/mat_spec_006_source_inventory.json"
SPEC_PATH = "spec/mat-spec-006.v0.1.json"
SOURCE_SHA256 = "06c405f1b13f90c2bd83322c512e116dafcf1f8e281618a59c3fcd4cf1510a04"
CAMPAIGN = "LIPA_CHUI_1983_1984"
COLUMNS = (
    "row_id", "source_table", "delta_T_microkelvin",
    "heat_capacity_J_per_mol_K", "table_side",
)
EXPECTED_IDS = tuple(f"B{i:02d}" for i in range(1, 7)) + tuple(
    f"A{i:02d}" for i in range(1, 7)
)
OUTPUT_NAMES = frozenset({
    "contract.json", "observations.json", "receiver-controls.csv",
    "source-audit.json", "heldout.json", "phase-gate.json", "manifest.json",
})
IMPLEMENTATION_PATHS = (
    "materials/mat_spec_006.py", "scripts/build_mat_spec_006.py",
)
# Frozen seven-artifact MAT-SPEC-005 baseline from merged-main CI.
PARENT_V5_SHA256 = {
    "audit.json": "0c74472e83808c466445a091be863083bc5f2f905c27b391980dc808d7d7f739",
    "contract.json": "15e7118fdc69d9d6e46be661fa14ef7f9f6965b31b4b5324fa303f79f051cdf6",
    "crossing.json": "c1c1287f61883ee940ed60e80e9b65457d34f90b330fcbb8219230582fadd40d",
    "manifest.json": "a88a0e5acca0824bd1471b9bf805acec0dcdf252a55fc435ae8671b21cf875bd",
    "observations.json": "34724d26f1ba76ca05139bcabb0468178d1004cc8988f56bf5a9e74fe2b8fdfd",
    "phase-gate.json": "f80bc1144b3f35e8f2a48c0debd735876aa6cbcb39b88dd7661d928df44a9661",
    "receiver-controls.csv": (
        "950a80a6398d37ff66049b77e0bacb900b9a5078a999e587a108aa9c8a5dc3ae"
    ),
}


EXPECTED_META = json.loads(
    "{\"profile\":\"MAT-SPEC-006\",\"source_id\":\"NASA-CR-177037-APPENDIX-A-"
    "1984\",\"source_title\":\"High Accuracy Heat Capacity Measurements th"
    "rough the Lambda Transition of Helium with Very High Temperature "
    "Resolution\",\"authors\":[\"William M. Fairbank\",\"John A. Lipa\"],\"app"
    "endix_authors\":[\"J. A. Lipa\",\"T. C. P. Chui\"],\"appendix_name\":\"Th"
    "e Heat Capacity of Liquid Helium Near the Lambda Transition, Data"
    " Release #1, January 15, 1984\",\"publication_year\":1984,\"nasa_docu"
    "ment_id\":\"19860021083\",\"source_url\":\"https://ntrs.nasa.gov/api/ci"
    "tations/19860021083/downloads/19860021083.pdf\",\"nasa_record\":\"htt"
    "ps://ntrs.nasa.gov/citations/19860021083\",\"related_original_paper"
    "_doi\":\"10.1103/PhysRevLett.51.2291\",\"source_excerpt\":\"Appendix A,"
    " Table 1 (above lambda), Table 2 (below lambda)\",\"source_pdf_page"
    "_indices\":{\"table_1\":40,\"table_2\":41},\"conditions\":\"helium-4, sat"
    "urated vapour pressure, approximately 3 mm high sample\",\"table_te"
    "mperature_definition\":\"temperature minus T_lambda; published micr"
    "odegrees (microkelvin offsets); not absolute kelvin\",\"table_prope"
    "rty\":\"gravity-corrected, averaged experimental heat capacity, J/("
    "mol K)\",\"data_kind\":\"experimenters' reported gravity-corrected an"
    "d averaged results, not raw acquisition files\",\"per_row_uncertain"
    "ty\":\"not reported for these twelve selected rows; absent is null,"
    " not zero\",\"calibration_limit\":\"authors discuss potential systema"
    "tic calibration and calorimeter errors; no row-level error distri"
    "butions supplied\",\"transcription\":\"12 manually selected published"
    " numeric facts, six nearest-ish rows from each side, leading zero"
    "s normalized; not an exhaustive table\",\"independence_from_mat_spe"
    "c_005\":\"NOT_ESTABLISHED; 1998 Donnelly-Barenghi compilation cites"
    " earlier Lipa results; distinct document does not establish indep"
    "endent experimental ancestry\",\"phase_labels\":\"ABOVE/BELOW derived"
    " from source table captions and signed delta T; not independently"
    " measured phase diagnostics\",\"rights\":\"NASA-hosted contractor rep"
    "ort labeled public-use permitted; attribution retained; no PDF re"
    "distributed\",\"source_data_sha256\":\"06c405f1b13f90c2bd83322c512e11"
    "6dafcf1f8e281618a59c3fcd4cf1510a04\"}"
)
EXPECTED_INVENTORY = json.loads(
    "{\"profile\":\"MAT-SPEC-006\",\"version\":\"0.1.0\",\"research_question\":\""
    "What additional physical data are required to validate a source-s"
    "eparated helium phase witness?\",\"sources\":[{\"id\":\"NASA-CR-177037-"
    "APPENDIX-A-1984\",\"role\":\"SOURCE_NUMERIC_EXCERPT\",\"kind\":\"PRIMARY_"
    "EXPERIMENT_CORRECTED_AVERAGED\",\"source_group\":\"LIPA_CHUI_1983_198"
    "4\",\"available\":\"TWELVE_REVIEWED_ROWS\",\"above_and_below\":true,\"per"
    "_row_error\":false,\"independent_diagnostic\":false,\"heldout_indepen"
    "dence_from_005\":\"NOT_ESTABLISHED\",\"url\":\"https://ntrs.nasa.gov/ci"
    "tations/19860021083\"},{\"id\":\"DONNELLY_BARENGHI_1998\",\"role\":\"FROZ"
    "EN_PARENT_REFERENCE\",\"kind\":\"EVALUATED_COMPILATION\",\"source_group"
    "\":\"REUSES_EARLIER_HELIUM_MEASUREMENTS\",\"available\":\"MAT_SPEC_005_"
    "FROZEN\",\"above_and_below\":true,\"per_row_error\":false,\"independent"
    "_diagnostic\":false,\"heldout_independence_from_1984\":\"NOT_ESTABLIS"
    "HED\",\"doi\":\"10.1063/1.556028\"},{\"id\":\"LIPA_1996_MICROGRAVITY\",\"ro"
    "le\":\"CANDIDATE_ONLY\",\"kind\":\"DIFFERENT_EXPERIMENT_PUBLICATION\",\"s"
    "ource_group\":\"LIPA_MICROGRAVITY_1992\",\"available\":\"PUBLICATION_AB"
    "STRACT_NOT_ROW_ADMITTED\",\"above_and_below\":true,\"per_row_error\":f"
    "alse,\"independent_diagnostic\":false,\"heldout_independence_from_19"
    "84\":\"REQUIRES_ORIGINAL_RUN_AND_SOURCE_AUDIT\",\"doi\":\"10.1103/PhysR"
    "evLett.76.944\"},{\"id\":\"LIPA_2003_ORBIT\",\"role\":\"CANDIDATE_ONLY\",\""
    "kind\":\"MICROGRAVITY_MEASUREMENT_REPORT\",\"source_group\":\"LIPA_MICR"
    "OGRAVITY_1992\",\"available\":\"PUBLICATION_ABSTRACT_NOT_ROW_ADMITTED"
    "\",\"above_and_below\":true,\"per_row_error\":false,\"independent_diagn"
    "ostic\":false,\"heldout_independence_from_1996\":\"OVERLAPPING_EXPERI"
    "MENTAL_CAMPAIGN\",\"doi\":\"10.1103/PhysRevB.68.174518\"},{\"id\":\"MAREK"
    "_LIPA_PHILIPS_1988\",\"role\":\"CANDIDATE_ONLY\",\"kind\":\"SECOND_SOUND_"
    "MEASUREMENT\",\"source_group\":\"STANFORD_MAREK_LIPA_1988\",\"available"
    "\":\"PUBLICATION_ABSTRACT_NOT_ROW_ADMITTED\",\"above_and_below\":false"
    ",\"per_row_error\":false,\"independent_diagnostic\":false,\"heldout_in"
    "dependence_from_1984\":\"NOT_ESTABLISHED\",\"doi\":\"10.1103/PhysRevB.3"
    "8.4465\"}],\"no_independence_assumption\":\"Shared authors, compilati"
    "on lineage, experiments and reference interpolation require revie"
    "w; no title/DOI-count independence surrogate.\"}"
)
EXPECTED_SPEC = json.loads(
    "{\"profile\":\"MAT-SPEC-006\",\"version\":\"0.1.0\",\"name\":\"Primary calor"
    "imetry evidence and source-separated validation preflight\",\"paren"
    "t_profile\":\"MAT-SPEC-005 v0.1.0\",\"parent_commit\":\"5b4c89b795beb7f"
    "c8c4f7d86ce2a2fb510cb6cb2\",\"foundational_record_doi\":\"10.5281/zen"
    "odo.24062652\",\"source_id\":\"NASA-CR-177037-APPENDIX-A-1984\",\"sourc"
    "e_data_sha256\":\"06c405f1b13f90c2bd83322c512e116dafcf1f8e281618a59"
    "c3fcd4cf1510a04\",\"row_count\":12,\"source_groups\":1,\"numeric_input\""
    ":\"reported microkelvin signed offset, gravity-corrected and avera"
    "ged C_s J/(mol K)\",\"physical_label\":\"table caption ABOVE/BELOW, N"
    "OT independent phase diagnosis\",\"symbolic_scale\":\"5 Hz/(J/mol K),"
    " authored, not a physical sound frequency\",\"uncertainty\":\"missing"
    " per row, null, no zero imputation\",\"split_protocol\":\"future stud"
    "y-level source-frozen holdout, no row leakage, independent physic"
    "al diagnostic labels, per-row positive errors, lineage audit\",\"re"
    "trospective_status\":\"protocol written after inspection of the 198"
    "4 table; not preregistered relative to this dataset\",\"holdout_acc"
    "uracy\":\"never compute from published table-side context or synthe"
    "tic test fixtures\",\"invalid_source_independence\":\"MAT-SPEC-005 co"
    "mpilation and 1984 report may share experimental lineage\",\"output"
    "_rule\":\"canonical ASCII JSON and CSV only; no WAV, PCM, other sam"
    "pled audio or MIDI playback\",\"missingness\":\"never fabricate measu"
    "red phase absence, per-row uncertainties or absolute Kelvin tempe"
    "ratures\",\"source_rights\":\"source numerical facts excerpted with a"
    "ttribution; original publication rights retained\"}"
)


def _decimal(value: str, *, signed: bool = False) -> Fraction:
    """Reject exponent, whitespace, fractions, booleans and ambiguous zeros."""
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("invalid reported decimal")
    pattern = r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?" if signed else (
        r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?"
    )
    if not re.fullmatch(pattern, value):
        raise ValueError("invalid reported decimal")
    return Fraction(value)


def parse_measurements(raw: bytes) -> list[dict]:
    """Parse only the pinned, visually checked Appendix A table extract."""
    if mat_spec.sha256(raw) != SOURCE_SHA256:
        raise ValueError("primary table source SHA-256 mismatch")
    try:
        table = list(csv.reader(io.StringIO(raw.decode("ascii")), strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("invalid primary table encoding") from exc
    if (
        len(table) != 13
        or tuple(table[0]) != COLUMNS
        or any(len(row) != len(COLUMNS) for row in table)
        or tuple(row[0] for row in table[1:]) != EXPECTED_IDS
    ):
        raise ValueError("primary table row/header membership drift")
    output = []
    for row in table[1:]:
        identifier, src_table, temp, heat, side = row
        delta = _decimal(temp, signed=True)
        capacity = _decimal(heat)
        expected = (
            "APPENDIX_A_TABLE_2" if side == "BELOW"
            else "APPENDIX_A_TABLE_1" if side == "ABOVE" else None
        )
        if (
            expected is None or expected != src_table
            or (side == "BELOW") != (delta < 0)
            or capacity <= 0
            or delta == 0
        ):
            raise ValueError("source table phase-context or numeric invariant drift")
        output.append({
            "row_id": identifier,
            "source_table": src_table,
            "delta_T_microkelvin": temp,
            "heat_capacity_J_per_mol_K": heat,
            "table_side_context": side,
            "source_campaign_id": CAMPAIGN,
            "physical_helium_condition": "SATURATED_VAPOUR_PRESSURE_HELIUM_4",
            "measurement_status": "EXPERIMENTALLY_REPORTED_GRAVITY_CORRECTED_AVERAGED",
            "row_uncertainty_J_per_mol_K": None,
            "independent_physical_phase_diagnostic": None,
            "independent_phase_label": None,
            "temperature_absolute_K": None,
            "source_table_side_is_independent_label": False,
            "reported_source_id": "NASA-CR-177037-APPENDIX-A-1984",
        })
    if not all(
        Fraction(a["delta_T_microkelvin"]) < Fraction(b["delta_T_microkelvin"])
        for a, b in pairwise(output)
    ):
        raise ValueError("source temperature offset order drift")
    return output


def map_receivers(observations: list[dict], scale: Fraction = Fraction(5)) -> list[dict]:
    """Author one physical-unit-consistent positive scale, no sampled audio."""
    if not isinstance(scale, Fraction) or scale <= 0:
        raise ValueError("receiver scale must be an exact positive fraction")
    result = []
    for row in observations:
        c = _decimal(row["heat_capacity_J_per_mol_K"])
        target = c * scale
        midi = mat_spec.nearest_midi(target)
        result.append({
            "row_id": row["row_id"],
            "delta_T_microkelvin": row["delta_T_microkelvin"],
            "table_side_context": row["table_side_context"],
            "heat_capacity_J_per_mol_K": row["heat_capacity_J_per_mol_K"],
            "reported_uncertainty_J_per_mol_K": None,
            "frequency_target_Hz": str(target),
            "nearest_midi_note": midi,
            "quantization_error_cents": (
                None if midi is None else mat_spec.cents_error(target, midi)
            ),
            "author_scale_Hz_per_J_per_mol_K": str(scale),
            "phase_label_provenance": "TABLE_SIDE_ONLY_NOT_INDEPENDENT_WITNESS",
        })
    return result


def _control_csv(rows: list[dict]) -> bytes:
    s = io.StringIO(newline="")
    w = csv.DictWriter(s, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return s.getvalue().encode("ascii")


def source_numerical_audit(observations: list[dict], mapped: list[dict]) -> dict:
    """Descriptive arithmetic on published rounded/averaged measurements only."""
    if len(observations) != 12 or len(mapped) != 12:
        raise ValueError("expected 12 reviewed rows")
    before = [r for r in observations if r["table_side_context"] == "BELOW"]
    after = [r for r in observations if r["table_side_context"] == "ABOVE"]
    if len(before) != 6 or len(after) != 6:
        raise ValueError("source side coverage mismatch")
    for row, mapped_row in zip(observations, mapped, strict=True):
        if row["row_id"] != mapped_row["row_id"]:
            raise ValueError("receiver row association drift")
        if (
            Fraction(mapped_row["frequency_target_Hz"]) / 5
            != Fraction(row["heat_capacity_J_per_mol_K"])
        ):
            raise ValueError("exact source-target roundtrip failure")
        if row["row_uncertainty_J_per_mol_K"] is not None:
            raise ValueError("forged source measurement uncertainty")
        if (
            row["independent_physical_phase_diagnostic"] is not None
            or row["independent_phase_label"] is not None
        ):
            raise ValueError("unverified physical phase witness")
    near_below, near_above = before[-1], after[0]
    values = [Fraction(x["heat_capacity_J_per_mol_K"]) for x in observations]
    notes = [x["nearest_midi_note"] for x in mapped]
    return {
        "profile": PROFILE, "version": VERSION,
        "measured_and_processed_source_rows": len(observations),
        "below_context_rows": len(before), "above_context_rows": len(after),
        "distinct_reported_values": len(set(values)),
        "exact_fraction_roundtrip_checks": len(mapped),
        "receiver_distinct_midi_notes": len(set(notes)),
        "receiver_colliding_row_pairs": sum(
            a == b for a, b in combinations(notes, 2)
        ),
        "closest_selected_below_microK": near_below["delta_T_microkelvin"],
        "closest_selected_above_microK": near_above["delta_T_microkelvin"],
        "closest_selected_heat_capacity_difference_J_mol_K": str(
            Fraction(near_above["heat_capacity_J_per_mol_K"])
            - Fraction(near_below["heat_capacity_J_per_mol_K"])
        ),
        "near_pair_offsets_equal_magnitude": False,
        "source_reports_individual_row_uncertainty": False,
        "infer_transition_jump_or_significance": False,
        "calibrated_phase_accuracy": None,
        "receiver_audio_generated": False,
    }


def check_future_split_structure(rows: list[dict]) -> dict:
    """Structural preflight for future externally audited, source-level splits.

    This is NOT an authentication of investigator identity, physical labels or
    source independence. Never return a scientific validation result here.
    """
    reasons = []
    if not rows:
        return {"status": "BLOCKED", "reasons": ["EMPTY_CANDIDATE"]}
    train = [r for r in rows if r.get("split") == "TRAIN"]
    heldout = [r for r in rows if r.get("split") == "HOLDOUT"]
    if len(train) + len(heldout) != len(rows) or not train or not heldout:
        reasons.append("TRAIN_HOLDOUT_PARTITIONS_REQUIRED")
    train_ids = {r.get("source_id") for r in train}
    heldout_ids = {r.get("source_id") for r in heldout}
    families_train = {r.get("experimental_family_id") for r in train}
    families_holdout = {r.get("experimental_family_id") for r in heldout}
    if train_ids & heldout_ids or families_train & families_holdout:
        reasons.append("SOURCE_LINEAGE_LEAKAGE")
    if None in train_ids | heldout_ids or None in families_train | families_holdout:
        reasons.append("MISSING_SOURCE_IDENTITY")
    if not any(r.get("phase") == "HE_I" for r in train) or not any(
        r.get("phase") == "HE_II" for r in train
    ):
        reasons.append("TRAIN_REQUIRES_BOTH_PHASES")
    if not any(r.get("phase") == "HE_I" for r in heldout) or not any(
        r.get("phase") == "HE_II" for r in heldout
    ):
        reasons.append("HOLDOUT_REQUIRES_BOTH_PHASES")
    if len({r.get("row_id") for r in rows}) != len(rows):
        reasons.append("DUPLICATE_ROW_ID")
    for r in rows:
        if (
            r.get("phase") not in {"HE_I", "HE_II"}
            or r.get("label_basis") != "INDEPENDENT_PHYSICAL_DIAGNOSTIC"
            or r.get("diagnostic_type") not in {
                "SECOND_SOUND_DIRECT_DETECTION",
                "INDEPENDENT_SUPERFLUID_FRACTION_MEASUREMENT",
            }
        ):
            reasons.append("CIRCULAR_OR_UNVERIFIED_PHASE_LABEL")
        try:
            sigma = _decimal(str(r.get("measurement_uncertainty")))
            diagnostic_sigma = _decimal(str(r.get("diagnostic_uncertainty")))
            if sigma <= 0 or diagnostic_sigma <= 0:
                raise ValueError("zero error")
        except ValueError:
            reasons.append("MISSING_POSITIVE_CALIBRATED_UNCERTAINTY")
        if (
            not r.get("pressure_condition")
            or not r.get("provenance_hash")
            or not re.fullmatch(r"[0-9a-f]{64}", str(r.get("provenance_hash")))
        ):
            reasons.append("UNBOUND_PHYSICAL_CONDITIONS_OR_PROVENANCE")
        if r.get("synthetic_fixture") is True:
            reasons.append("SYNTHETIC_NOT_PHYSICAL_EVIDENCE")
    reasons = sorted(set(reasons))
    return {
        "status": "STRUCTURAL_ONLY_NOT_EMPIRICAL_ADMISSION" if not reasons else "BLOCKED",
        "reasons": reasons,
        "train_rows": len(train), "heldout_rows": len(heldout),
        "physical_validation_admitted": False,
        "holdout_accuracy": None,
        "independence_authenticated": False,
        "meaning": (
            "Structural preflight is not an audit of real-world source "
            "independence or independently observed phase labels"
        ),
    }


def phase_gate(observations: list[dict], inventory: dict) -> dict:
    """Preserve a meaningful primary-data advance without a fake holdout."""
    if (
        len(observations) != 12
        or len({r["source_campaign_id"] for r in observations}) != 1
        or {r["table_side_context"] for r in observations} != {"BELOW", "ABOVE"}
        or any(
            r["independent_phase_label"] is not None
            or r["independent_physical_phase_diagnostic"] is not None
            or r["row_uncertainty_J_per_mol_K"] is not None
            or r["source_table_side_is_independent_label"] is not False
            or r["measurement_status"] != (
                "EXPERIMENTALLY_REPORTED_GRAVITY_CORRECTED_AVERAGED"
            )
            for r in observations
        )
    ):
        raise ValueError("forged experimental witness or drift")
    studies = inventory["sources"]
    if not (
        len(studies) == 5
        and studies[0]["id"] == "NASA-CR-177037-APPENDIX-A-1984"
        and studies[1]["id"] == "DONNELLY_BARENGHI_1998"
        and studies[0]["heldout_independence_from_005"] == "NOT_ESTABLISHED"
        and studies[0]["per_row_error"] is False
    ):
        raise ValueError("source lineage risk omitted")
    return {
        "primary_corrected_measurement_excerpts": "REPLAY_VERIFIED",
        "independent_experimental_phase_validation": "BLOCKED",
        "source_lineage_assurance": "INDEPENDENCE_FROM_MAT_SPEC_005_NOT_ESTABLISHED",
        "experiment_campaigns_with_admitted_numeric_rows": 1,
        "primary_table_context_count": {"below": 6, "above": 6},
        "independent_diagnostic_phase_labels": 0,
        "positive_per_row_measured_uncertainties": 0,
        "source_separated_train_campaigns": 0,
        "source_separated_holdout_campaigns": 0,
        "phase_classifier_trained": False,
        "phase_holdout_accuracy": None,
        "blinded_listener_discrimination": None,
        "critical_exponent_from_006": None,
        "reasons": [
            "ONE_EXPERIMENTAL_CAMPAIGN_NOT_SOURCE_SEPARATED",
            "POTENTIAL_1984_LINEAGE_OVERLAP_WITH_1998_COMPILATION",
            "NO_ORTHOGONAL_INDEPENDENT_PHASE_LABELS",
            "NO_PER_ROW_EXPERIMENTAL_UNCERTAINTY_OR_COVARIANCE",
            "NO_PREREGISTERED_HELD_OUT_EXPERIMENT",
        ],
        "narrow_physical_claim": (
            "A primary publication's processed experimental heat-capacity "
            "values cover both sides of the established lambda transition"
        ),
    }


def build_evidence(root: Path) -> dict[str, bytes]:
    """Rebuild all frozen ancestors, then export only independently scoped 006."""
    parent = mat_spec_005.build_evidence(root)
    if set(parent) != mat_spec_005.OUTPUT_NAMES:
        raise ValueError("MAT-SPEC-005 parent membership mismatch")
    parent_hashes = {name: mat_spec.sha256(raw) for name, raw in parent.items()}
    if parent_hashes != PARENT_V5_SHA256:
        raise ValueError("MAT-SPEC-005 frozen output SHA-256 mismatch")
    ancestor_manifest = json.loads(parent["manifest.json"])
    if (
        ancestor_manifest.get("profile") != "MAT-SPEC-005"
        or ancestor_manifest.get("version") != "0.1.0"
        or ancestor_manifest.get("parent_commit") != mat_spec_005.PARENT_COMMIT
        or ancestor_manifest.get("original_mat_spec_001_doi") != PARENT_DOI
    ):
        raise ValueError("frozen MAT-SPEC-005 lineage mismatch")
    if any(
        name not in parent or mat_spec.sha256(parent[name]) != info["sha256"]
        for name, info in ancestor_manifest["outputs"].items()
    ):
        raise ValueError("frozen MAT-SPEC-005 manifest inconsistent")
    source = mat_spec.read_regular(root / DATA_PATH)
    meta_bytes = mat_spec.read_regular(root / META_PATH)
    inventory_bytes = mat_spec.read_regular(root / INVENTORY_PATH)
    spec_bytes = mat_spec.read_regular(root / SPEC_PATH)
    meta = json.loads(meta_bytes)
    inventory = json.loads(inventory_bytes)
    spec = json.loads(spec_bytes)
    if meta != EXPECTED_META or inventory != EXPECTED_INVENTORY or spec != EXPECTED_SPEC:
        raise ValueError("MAT-SPEC-006 frozen contract or source catalogue drift")
    obs = parse_measurements(source)
    mapped = map_receivers(obs)
    numerical = source_numerical_audit(obs, mapped)
    gate = phase_gate(obs, inventory)
    heldout = {
        "protocol": "MAT-SPEC-006-FUTURE-PHASE-HOLDOUT/v1",
        "protocol_timing": (
            "planned after examining 1984 and 1998 sources; NOT a "
            "preregistration for the present data"
        ),
        "split_unit": "distinct experimentally independent campaigns, never rows",
        "candidate_corpus": "NOT_ADMITTED",
        "source_independence": gate["source_lineage_assurance"],
        "phase_labels": "REQUIRE_NON_TEMPERATURE_INDEPENDENT_DIAGNOSTIC",
        "calibrated_uncertainty": "REQUIRED_PER_ROW",
        "physical_phase_heldout_accuracy": None,
        "classifier_training": "NOT_PERFORMED",
        "blind_predictions": None,
        "synthetic_structure_checks": "UNIT_TEST_ONLY_NOT_PERSISTED_AS_PHYSICS",
        "status": "BLOCKED_AWAITING_INDEPENDENT_SOURCE_WITNESSES",
    }
    products = {
        "contract.json": mat_spec.canonical_json(spec),
        "observations.json": mat_spec.canonical_json({
            "metadata": meta, "observations": obs,
        }),
        "receiver-controls.csv": _control_csv(mapped),
        "source-audit.json": mat_spec.canonical_json({
            "numeric": numerical, "inventory": inventory,
        }),
        "heldout.json": mat_spec.canonical_json(heldout),
        "phase-gate.json": mat_spec.canonical_json(gate),
    }
    impl = {
        name: mat_spec.sha256(mat_spec.read_regular(root / name))
        for name in IMPLEMENTATION_PATHS
    }
    receipt = {
        "profile": PROFILE, "version": VERSION,
        "source": {"path": DATA_PATH, "sha256": mat_spec.sha256(source),
                   "bytes": len(source), "id": meta["source_id"]},
        "parent": {
            "commit": PARENT_COMMIT,
            "artifacts": {
                name: {"sha256": digest, "bytes": len(parent[name])}
                for name, digest in sorted(parent_hashes.items())
            },
            "foundational_doi": PARENT_DOI,
        },
        "metadata_sha256": mat_spec.sha256(meta_bytes),
        "inventory_sha256": mat_spec.sha256(inventory_bytes),
        "contract_sha256": mat_spec.sha256(spec_bytes),
        "implementation": impl,
        "outputs": {
            name: {"sha256": mat_spec.sha256(raw), "bytes": len(raw)}
            for name, raw in sorted(products.items())
        },
        "canonical": "ASCII sorted compact JSON LF and CSV LF; no clock",
        "manifest_self_hash": None,
        "canonical_pcm_sha256": None, "canonical_wav_sha256": None,
        "audio_generated": False,
    }
    products["manifest.json"] = mat_spec.canonical_json(receipt)
    return products


def write_evidence(root: Path, destination: str, products: dict[str, bytes]) -> Path:
    """Anchored POSIX O_NOFOLLOW / O_EXCL symbolic-only export."""
    path = PurePosixPath(destination)
    if (
        not destination or path.is_absolute() or "\\" in destination
        or any(piece in {"", ".", ".."} for piece in destination.split("/"))
    ):
        raise ValueError("destination must be fresh and relative")
    if set(products) != OUTPUT_NAMES or any(
        PurePosixPath(name).name != name
        or Path(name).suffix not in {".json", ".csv"} for name in products
    ):
        raise ValueError("non-symbolic artifact denied")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fds = [os.open(root, flags)]
    try:
        for piece in path.parts[:-1]:
            with suppress(FileExistsError):
                os.mkdir(piece, mode=0o755, dir_fd=fds[-1])
            fds.append(os.open(piece, flags, dir_fd=fds[-1]))
        parent = fds[-1]
        os.mkdir(path.parts[-1], mode=0o755, dir_fd=parent)
        fds.append(os.open(path.parts[-1], flags, dir_fd=parent))
        out = fds[-1]
        for name in sorted(products):
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode=0o644, dir_fd=out,
            )
            with os.fdopen(fd, "wb") as target:
                target.write(products[name])
        actual = os.fstat(out)
        visible = os.stat(path.parts[-1], dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISDIR(visible.st_mode) or (
            actual.st_dev, actual.st_ino
        ) != (visible.st_dev, visible.st_ino):
            raise ValueError("output directory was replaced during export")
    finally:
        for fd in reversed(fds):
            os.close(fd)
    return root / path
