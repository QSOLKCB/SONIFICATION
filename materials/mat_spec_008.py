"""MAT-SPEC-008: original-experiment evidence acquisition and independence gate.

SPDX-License-Identifier: MPL-2.0
Copyright (c) 2026 Trent Slade / QSOL-IMC.

This is a source availability and measurement-provenance audit, not physical
replication, classifier evaluation, or generated sampled audio.
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
from itertools import combinations
from pathlib import Path, PurePosixPath

from materials import mat_spec, mat_spec_006, mat_spec_007

PROFILE = "MAT-SPEC-008"
VERSION = "0.1.0"
PARENT_COMMIT = "b97348ff8fcf3f57764dec21a8914f153f96a745"
FOUNDATIONAL_DOI = "10.5281/zenodo.24062652"
SOURCE_PATH = "data/materials/helium4/mat_spec_008_source_catalogue.json"
SPEC_PATH = "spec/mat-spec-008.v0.1.json"
CATALOGUE_SHA256 = None  # Set to independent source-file SHA from GitHub CI.
CAMPAIGNS = ("AL71_SVP", "GM75_SVP", "LC83_SVP", "STS52_1992")
FAMILIES = {
    "AL71_SVP": "BELL_AHLERS",
    "GM75_SVP": "MINNESOTA_GASPARINI_MOLDOVER",
    "LC83_SVP": "STANFORD_LIPA",
    "STS52_1992": "STANFORD_LIPA",
}
DOC_IDS = (
    "LC83_NASA_1984", "AHLERS_PRA_1971", "MUELLER_PRB_1976",
    "GASPARINI_MOLDOVER_PRB_1975", "GASPARINI_GAETA_PRB_1978",
    "STS52_NASA_1994", "STS52_PRL_1996", "STS52_PRB_2003",
    "DONNELLY_BARENGHI_1998", "BARMATZ_RMP_2007",
)
OUTPUT_NAMES = frozenset({
    "contract.json", "source-catalogue.json", "campaigns.csv",
    "candidate-pairs.csv", "measurement-audit.json", "admission.json",
    "protocol.json", "manifest.json",
})
IMPLEMENTATION_PATHS = (
    "materials/mat_spec_008.py", "scripts/build_mat_spec_008.py",
)
# Capture eight frozen MAT-SPEC-007 artifact SHA-256 values from successful
# merged-main CI and require exact equality before making review-ready.
PARENT_V7_SHA256: dict[str, str] | None = None


def _identity(value: object) -> str:
    if (
        not isinstance(value, str) or not value or len(value) > 100
        or value != value.strip() or re.fullmatch(r"[A-Z0-9_]+", value) is None
    ):
        raise ValueError("invalid or empty source experiment identity")
    return value


def parse_catalogue(raw: bytes) -> dict:
    """Strict membership/lineage check; neither a PDF nor remote data fetch."""
    if CATALOGUE_SHA256 is not None and mat_spec.sha256(raw) != CATALOGUE_SHA256:
        raise ValueError("MAT-SPEC-008 source catalogue SHA-256 mismatch")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("invalid source-catalogue JSON") from exc
    if (
        data != EXPECTED_CATALOGUE
        or data.get("profile") != PROFILE
        or data.get("version") != VERSION
        or len(data.get("source_docs", [])) != len(DOC_IDS)
    ):
        raise ValueError("MAT-SPEC-008 frozen source catalogue mismatch")
    docs = data["source_docs"]
    if tuple(d["doc_id"] for d in docs) != DOC_IDS:
        raise ValueError("source catalogue identity drift")
    if len({d["doc_id"] for d in docs}) != len(DOC_IDS):
        raise ValueError("duplicate source document ID")
    for d in docs:
        _identity(d["doc_id"])
        campaign = d["campaign"]
        if campaign is None:
            if d["document_kind"] not in {"EVALUATED_COMPILATION", "SECONDARY_FIT_REVIEW"}:
                raise ValueError("unassigned experiment identity")
        elif _identity(campaign) not in CAMPAIGNS:
            raise ValueError("unrecognized experiment campaign")
        if campaign and d["lab_family"] != FAMILIES[campaign]:
            raise ValueError("source-family mismatch")
        if not isinstance(d["source_bound_measurement_rows"], int):
            raise ValueError("invalid claimed original numeric row count")
        if (
            d["source_bound_measurement_rows"] < 0
            or d["per_row_calibrated_uncertainty"] is not False
            or d["orthogonal_phase_diagnostic"] is not False
        ):
            raise ValueError("forged admitted evidence flags")
    return data


def source_audit(
    catalogue: dict, actual_measurement_rows: list[dict], fit_summaries: list[dict]
) -> tuple[list[dict], list[dict], dict]:
    """Do not promote a literature DOI or reanalysis to a measured campaign."""
    docs = catalogue["source_docs"]
    if (
        len(actual_measurement_rows) != 12
        or len(fit_summaries) != 4
        or {r["source_campaign_id"] for r in actual_measurement_rows}
        != {mat_spec_006.CAMPAIGN}
        or tuple(r["acquisition_campaign"] for r in fit_summaries) != CAMPAIGNS
    ):
        raise ValueError("MAT-SPEC-006/007 original acquisition lineage drift")
    if any(
        r["row_uncertainty_J_per_mol_K"] is not None
        or r["independent_physical_phase_diagnostic"] is not None
        or r["independent_phase_label"] is not None
        for r in actual_measurement_rows
    ):
        raise ValueError("forged original row uncertainties or phase diagnostics")

    totals = {camp: 0 for camp in CAMPAIGNS}
    for d in docs:
        if d["source_bound_measurement_rows"]:
            if d["doc_id"] != "LC83_NASA_1984":
                raise ValueError("unsupported independent numeric measurements")
            totals["LC83_SVP"] += d["source_bound_measurement_rows"]
    if totals["LC83_SVP"] != len(actual_measurement_rows):
        raise ValueError("admitted NASA measurement count drift")
    campaigns = []
    for camp in CAMPAIGNS:
        records = [d for d in docs if d["campaign"] == camp]
        original = [d for d in records if d["document_kind"] in {
            "ORIGINAL_PROCESSED_MEASUREMENT_TABLE",
            "ORIGINAL_EXPERIMENT_PUBLICATION",
            "ORIGINAL_EXPERIMENT_CONFERENCE",
        }]
        if not original:
            raise ValueError("campaign has no attributed original experimental source")
        campaigns.append({
            "campaign": camp,
            "lab_family": FAMILIES[camp],
            "source_documents": len(records),
            "original_source_docs": len(original),
            "source_pinned_processed_measurement_rows": totals[camp],
            "per_row_calibrated_uncertainties": 0,
            "independent_phase_diagnostic_rows": 0,
            "acquisition_run_independence_attested": False,
            "admission_status": "BLOCKED_NO_INDEPENDENT_MEASUREMENT_PACKET",
        })
    pairs = []
    for a, b in combinations(campaigns, 2):
        pairs.append({
            "campaign_a": a["campaign"], "campaign_b": b["campaign"],
            "distinct_published_campaigns": True,
            "different_lab_family": a["lab_family"] != b["lab_family"],
            "both_have_source_pinned_original_measurements": (
                a["source_pinned_processed_measurement_rows"] > 0
                and b["source_pinned_processed_measurement_rows"] > 0
            ),
            "experiment_run_independence_attested": False,
            "eligible_for_independent_replication": False,
        })
    if (
        len(pairs) != 6 or sum(x["different_lab_family"] for x in pairs) != 5
        or sum(x["both_have_source_pinned_original_measurements"] for x in pairs) != 0
    ):
        raise ValueError("independence pair conservation failure")
    report = {
        "profile": PROFILE, "version": VERSION,
        "reviewed_publication_documents": len(docs),
        "published_original_acquisition_campaigns": len(campaigns),
        "distinct_lab_families": len(set(FAMILIES.values())),
        "original_source_pinned_processed_measurement_campaigns": sum(
            x["source_pinned_processed_measurement_rows"] > 0 for x in campaigns
        ),
        "source_pinned_processed_measurement_rows": len(actual_measurement_rows),
        "available_row_level_calibrated_uncertainties": 0,
        "available_independent_phase_diagnostic_rows": 0,
        "secondary_review_fitted_records": len(fit_summaries),
        "candidate_campaign_pairs": len(pairs),
        "candidate_cross_lab_pairs": 5,
        "measurement_level_replicable_pairs": 0,
        "do_not_add_reanalyses_as_new_experiments": True,
        "different_publications_not_independent_measurement_packets": True,
    }
    return campaigns, pairs, report


def _rows_csv(rows: list[dict]) -> bytes:
    out = io.StringIO(newline="")
    fields = tuple(rows[0])
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("ascii")


def _decimal(value: object) -> Fraction:
    if not isinstance(value, str) or re.fullmatch(
        r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value
    ) is None:
        raise ValueError("missing or invalid positive calibrated quantity")
    number = Fraction(value)
    if number <= 0:
        raise ValueError("missing or zero calibrated quantity")
    return number


def validate_future_measurement_packet(records: list[dict]) -> dict:
    """Structure only; caller assertions cannot prove real-world measurements."""
    reasons: set[str] = set()
    if not records:
        return {
            "status": "BLOCKED", "reasons": ["EMPTY_MEASUREMENT_PACKET"],
            "physical_evidence_admitted": False, "independence_authenticated": False,
        }
    experiment_to_lab: dict[str, str] = {}
    experiment_to_source: dict[str, str] = {}
    experiment_to_hash: dict[str, str] = {}
    run_to_campaign: dict[str, str] = {}
    document_to_campaign: dict[str, str] = {}
    hash_to_campaign: dict[str, str] = {}
    phases_by_campaign: dict[str, set[str]] = {}
    seen_rows = set()
    campaigns = set()
    labs = set()
    for row in records:
        try:
            camp = _identity(row.get("campaign_id"))
            lab = _identity(row.get("lab_family_id"))
            run = _identity(row.get("original_run_id"))
            doc = _identity(row.get("source_document_id"))
            identifier = _identity(row.get("row_id"))
        except ValueError:
            reasons.add("MISSING_OR_INVALID_SOURCE_IDENTITIES")
            continue
        if identifier in seen_rows:
            reasons.add("DUPLICATE_MEASUREMENT_ROW_ID")
        seen_rows.add(identifier)
        campaigns.add(camp)
        labs.add(lab)
        if camp in experiment_to_lab and experiment_to_lab[camp] != lab:
            reasons.add("CAMPAIGN_LAB_IDENTITY_CONTRADICTION")
        experiment_to_lab[camp] = lab
        # Source, document and run identities must not migrate between
        # purportedly independent acquisition campaigns.
        source_key = doc + ":" + run
        if camp in experiment_to_source and experiment_to_source[camp] != source_key:
            reasons.add("CAMPAIGN_RUN_OR_DOCUMENT_INCONSISTENT")
        experiment_to_source[camp] = source_key
        for key, owner, prior in (
            ("REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS", run_to_campaign, run),
            ("REUSED_ORIGINAL_DOCUMENT_ACROSS_CAMPAIGNS", document_to_campaign, doc),
        ):
            if prior in owner and owner[prior] != camp:
                reasons.add(key)
            owner[prior] = camp
        phases_by_campaign.setdefault(camp, set()).add(row.get("phase"))
        if row.get("source_type") != "ORIGINAL_EXPERIMENTAL_RECORD":
            reasons.add("DERIVED_FIT_OR_COMPILATION_IS_NOT_PRIMARY_DATA")
        if row.get("synthetic_fixture") is True:
            reasons.add("SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT")
        if row.get("diagnostic_basis") != "INDEPENDENT_NON_TEMPERATURE_DIAGNOSTIC":
            reasons.add("CIRCULAR_OR_MISSING_PHASE_DIAGNOSTIC")
        if row.get("phase") not in {"HE_I", "HE_II"}:
            reasons.add("UNVERIFIED_PHASE_LABEL")
        try:
            _decimal(row.get("measurement_value"))
            _decimal(row.get("measurement_sigma"))
            _decimal(row.get("diagnostic_sigma"))
        except ValueError:
            reasons.add("MISSING_CALIBRATED_MEASUREMENT_UNCERTAINTY")
        digest = row.get("source_sha256")
        if (
            not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or row.get("pressure_condition") not in {
                "HE4_SVP", "DOCUMENTED_FIXED_PRESSURE"
            }
        ):
            reasons.add("SOURCE_HASH_OR_PHYSICAL_CONDITION_NOT_DOCUMENTED")
        else:
            if digest in hash_to_campaign and hash_to_campaign[digest] != camp:
                reasons.add("REUSED_SOURCE_BYTES_ACROSS_CAMPAIGNS")
            hash_to_campaign[digest] = camp
            if camp in experiment_to_hash and experiment_to_hash[camp] != digest:
                reasons.add("CAMPAIGN_SOURCE_BYTES_INCONSISTENT")
            experiment_to_hash[camp] = digest
    if any(phases != {"HE_I", "HE_II"} for phases in phases_by_campaign.values()):
        reasons.add("BOTH_PHASES_REQUIRED_FOR_EACH_CAMPAIGN")
    if len(campaigns) < 2 or len(labs) < 2:
        reasons.add("TWO_INDEPENDENT_CAMPAIGNS_AND_LABS_REQUIRED")
    if len(set(experiment_to_source.values())) < 2:
        reasons.add("DISTINCT_ORIGINAL_RUNS_REQUIRED")
    # Do not use the user's declared campaign strings as proof of independence.
    return {
        "status": "BLOCKED" if reasons else "STRUCTURAL_ONLY_UNAUTHENTICATED",
        "reasons": sorted(reasons),
        "candidate_rows": len(records),
        "described_campaigns": len(campaigns),
        "described_labs": len(labs),
        "physical_evidence_admitted": False,
        "independence_authenticated": False,
        "heldout_accuracy": None,
        "note": "A structural pass never authenticates original run bytes or phase labels",
    }


def evidence_admission(report: dict, catalogue: dict) -> dict:
    if (
        report["original_source_pinned_processed_measurement_campaigns"] != 1
        or report["source_pinned_processed_measurement_rows"] != 12
        or report["measurement_level_replicable_pairs"] != 0
        or report["available_row_level_calibrated_uncertainties"] != 0
        or report["available_independent_phase_diagnostic_rows"] != 0
    ):
        raise ValueError("unanticipated scientific admission state")
    return {
        "status": "BLOCKED_INSUFFICIENT_INDEPENDENT_MEASUREMENT_DATA",
        "source_catalogue_profile": catalogue["profile"],
        "one_campaign_processed_excerpt": "REPLAY_VERIFIED",
        "independent_experimental_replication": "NOT_DEMONSTRATED",
        "distinct_campaigns_described": 4,
        "independent_measurement_campaigns_with_source_pinned_rows": 1,
        "independent_measurement_campaign_pair_count": 0,
        "independently_verified_raw_acquisition_campaigns": 0,
        "train_test_split": "NOT_PERFORMED",
        "trained_phase_classifier": False,
        "physical_phase_accuracy": None,
        "source_separated_heldout_accuracy": None,
        "calibrated_error_comparison": "BLOCKED_NO_PER_ROW_ERRORS",
        "reasons": [
            "SECOND_INDEPENDENT_MEASUREMENT_LEVEL_CORPUS_NOT_ADMITTED",
            "PUBLISHED_ARTICLE_OR_REFIT_NOT_AN_ORIGINAL_ROW_PACKET",
            "NO_TWO_SOURCE_PINNED_CAMPAIGNS",
            "ORIGINAL_PROCESSED_MEASUREMENT_ROWS_LACK_PER_ROW_ERRORS",
            "NO_ORTHOGONAL_PHYSICAL_PHASE_LABELS",
            "NO_INDEPENDENT_ORIGINAL_RUN_IDENTITY_AUTHENTICATION",
            "NO_PREREGISTERED_SOURCE_SEPARATED_HELDOUT_EVALUATION",
        ],
        "next": "MAT-SPEC-009 may only attempt physical validation after independent admission",
        "program_end": "MAT-SPEC-010",
        "no_audio_generated": True,
    }


def build_evidence(root: Path) -> dict[str, bytes]:
    """Rebuild 001..007, verify source excerpt and export negative evidence."""
    parent = mat_spec_007.build_evidence(root)
    if set(parent) != mat_spec_007.OUTPUT_NAMES:
        raise ValueError("MAT-SPEC-007 parent artifact membership drift")
    hashes = {name: mat_spec.sha256(raw) for name, raw in parent.items()}
    if PARENT_V7_SHA256 is not None and hashes != PARENT_V7_SHA256:
        raise ValueError("frozen MAT-SPEC-007 parent output SHA-256 drift")
    manifest = json.loads(parent["manifest.json"])
    if (
        manifest.get("profile") != "MAT-SPEC-007"
        or manifest.get("version") != "0.1.0"
        or manifest.get("parent_commit") != mat_spec_007.PARENT_COMMIT
        or manifest.get("foundational_mat_spec_001_doi") != FOUNDATIONAL_DOI
    ):
        raise ValueError("unexpected MAT-SPEC-007 parent lineage")
    for name, entry in manifest["outputs"].items():
        if name not in parent or mat_spec.sha256(parent[name]) != entry["sha256"]:
            raise ValueError("MAT-SPEC-007 parent manifest inconsistency")
    raw_catalogue = mat_spec.read_regular(root / SOURCE_PATH)
    raw_spec = mat_spec.read_regular(root / SPEC_PATH)
    catalogue = parse_catalogue(raw_catalogue)
    try:
        contract = json.loads(raw_spec)
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError("invalid MAT-SPEC-008 contract") from exc
    if contract != EXPECTED_SPEC:
        raise ValueError("frozen MAT-SPEC-008 contract drift")
    original_bytes = mat_spec.read_regular(root / mat_spec_006.DATA_PATH)
    original = mat_spec_006.parse_measurements(original_bytes)
    fits = list(csv.DictReader(io.StringIO(parent["fit-summaries.csv"].decode("ascii"))))
    campaigns, pairs, report = source_audit(catalogue, original, fits)
    admission = evidence_admission(report, catalogue)
    protocol = {
        "status": "FUTURE_MEASUREMENT_PACKET_PREFLIGHT",
        "review_timing": "DESIGNED_AFTER_INSPECTING_EXISTING_SOURCES",
        "required": [
            "TWO_PROVEN_INDEPENDENT_ORIGINAL_MEASUREMENT_CAMPAIGNS",
            "ROW_LEVEL_MEASUREMENT_AND_DIAGNOSTIC_ERRORS",
            "NON_TEMPERATURE_DERIVED_PHASE_LABELS",
            "NO_SOURCE_RUN_OR_CROSS_LAB_DEPENDENCY",
            "SOURCE_PINNED_MEASUREMENT_PACKET_AND_CALIBRATION",
            "PREREGISTERED_SOURCE_SEPARATED_HELDOUT_PLAN",
        ],
        "synthetic_fixture_controls_are_empirical_evidence": False,
        "structural_pass_alone_can_admit_physics": False,
        "performance_score": None,
        "program_end": "MAT-SPEC-010",
    }
    products = {
        "contract.json": mat_spec.canonical_json(contract),
        "source-catalogue.json": mat_spec.canonical_json(catalogue),
        "campaigns.csv": _rows_csv(campaigns),
        "candidate-pairs.csv": _rows_csv(pairs),
        "measurement-audit.json": mat_spec.canonical_json(report),
        "admission.json": mat_spec.canonical_json(admission),
        "protocol.json": mat_spec.canonical_json(protocol),
    }
    implementation = {
        path: mat_spec.sha256(mat_spec.read_regular(root / path))
        for path in IMPLEMENTATION_PATHS
    }
    output_manifest = {
        "profile": PROFILE, "version": VERSION, "parent_commit": PARENT_COMMIT,
        "parent_outputs": {
            name: {"sha256": value, "bytes": len(parent[name])}
            for name, value in sorted(hashes.items())
        },
        "source_catalogue": {
            "path": SOURCE_PATH, "sha256": mat_spec.sha256(raw_catalogue),
            "bytes": len(raw_catalogue),
        },
        "original_measurement_excerpt": {
            "path": mat_spec_006.DATA_PATH,
            "sha256": mat_spec.sha256(original_bytes),
            "rows": len(original),
        },
        "contract": {"path": SPEC_PATH, "sha256": mat_spec.sha256(raw_spec)},
        "implementation": implementation,
        "outputs": {
            name: {"sha256": mat_spec.sha256(raw), "bytes": len(raw)}
            for name, raw in sorted(products.items())
        },
        "foundational_mat_spec_001_doi": FOUNDATIONAL_DOI,
        "serialization": "ASCII canonical sorted compact JSON LF, CSV LF",
        "manifest_self_hash": None,
        "canonical_pcm_sha256": None,
        "canonical_wav_sha256": None,
        "audio_generated": False,
    }
    products["manifest.json"] = mat_spec.canonical_json(output_manifest)
    return products


def write_evidence(root: Path, destination: str, products: dict[str, bytes]) -> Path:
    """Anchored no-follow exclusive symbolic-only output."""
    path = PurePosixPath(destination)
    if (
        not destination or path.is_absolute() or "\\" in destination
        or any(component in {"", ".", ".."} for component in destination.split("/"))
    ):
        raise ValueError("invalid symbolic output destination")
    if set(products) != OUTPUT_NAMES or any(
        PurePosixPath(name).name != name
        or Path(name).suffix not in {".csv", ".json"} for name in products
    ):
        raise ValueError("forbidden non-symbolic output membership")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fds = [os.open(root, flags)]
    try:
        for component in path.parts[:-1]:
            with suppress(FileExistsError):
                os.mkdir(component, mode=0o755, dir_fd=fds[-1])
            fds.append(os.open(component, flags, dir_fd=fds[-1]))
        parent_fd = fds[-1]
        os.mkdir(path.parts[-1], mode=0o755, dir_fd=parent_fd)
        fds.append(os.open(path.parts[-1], flags, dir_fd=parent_fd))
        output_fd = fds[-1]
        for name in sorted(products):
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode=0o644, dir_fd=output_fd,
            )
            with os.fdopen(fd, "wb") as target:
                target.write(products[name])
        opened = os.fstat(output_fd)
        visible = os.stat(path.parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISDIR(visible.st_mode) or (
            opened.st_dev, opened.st_ino
        ) != (visible.st_dev, visible.st_ino):
            raise ValueError("output directory changed during export")
    finally:
        for fd in reversed(fds):
            os.close(fd)
    return root / path

EXPECTED_CATALOGUE = json.loads(
    "{\"profile\":\"MAT-SPEC-008\",\"version\":\"0.1.0\",\"scope\":\"Source-"
    "pinned original helium-4 SVP temperature-series measurement "
    "packets from at least two independent acquisitions; an artic"
    "le citation, figure or fitted exponent is not an original me"
    "asurement packet\",\"review_date\":\"2026-11-09\",\"numeric_source"
    "\":\"MAT-SPEC-006 frozen 12-row Lipa-Chui 1984 Appendix A proc"
    "essed calorimetry extract\",\"parent_fit_source\":\"MAT-SPEC-007"
    " frozen four-row 2007 secondary review fit-summary table\",\"s"
    "ource_docs\":[{\"doc_id\":\"LC83_NASA_1984\",\"document_kind\":\"ORI"
    "GINAL_PROCESSED_MEASUREMENT_TABLE\",\"campaign\":\"LC83_SVP\",\"la"
    "b_family\":\"STANFORD_LIPA\",\"primary_doi\":\"10.1103/PhysRevLett"
    ".51.2291\",\"url\":\"https://ntrs.nasa.gov/citations/19860021083"
    "\",\"source_bound_measurement_rows\":12,\"per_row_calibrated_unc"
    "ertainty\":false,\"orthogonal_phase_diagnostic\":false,\"conditi"
    "on\":\"HE4_SVP\",\"scope_note\":\"1984 NASA-CR-177037 original Lip"
    "a-Chui gravity-corrected averaged table, not raw instrument "
    "stream\"},{\"doc_id\":\"AHLERS_PRA_1971\",\"document_kind\":\"ORIGIN"
    "AL_EXPERIMENT_PUBLICATION\",\"campaign\":\"AL71_SVP\",\"lab_family"
    "\":\"BELL_AHLERS\",\"primary_doi\":\"10.1103/PhysRevA.3.696\",\"url\""
    ":\"https://doi.org/10.1103/PhysRevA.3.696\",\"source_bound_meas"
    "urement_rows\":0,\"per_row_calibrated_uncertainty\":false,\"orth"
    "ogonal_phase_diagnostic\":false,\"condition\":\"HE4_SVP\",\"scope_"
    "note\":\"Original SVP calorimetry published; no per-row origin"
    "al numeric data acquired and hash-pinned by this profile\"},{"
    "\"doc_id\":\"MUELLER_PRB_1976\",\"document_kind\":\"MIXED_NEW_PRESS"
    "URE_EXPERIMENT_AND_SVP_REANALYSIS\",\"campaign\":\"AL71_SVP\",\"la"
    "b_family\":\"BELL_AHLERS\",\"primary_doi\":\"10.1103/PhysRevB.14.2"
    "096\",\"url\":\"https://doi.org/10.1103/PhysRevB.14.2096\",\"sourc"
    "e_bound_measurement_rows\":0,\"per_row_calibrated_uncertainty\""
    ":false,\"orthogonal_phase_diagnostic\":false,\"condition\":\"SVP_"
    "FIT_FROM_AHLERS_PRIOR_DATA;NEW_PRESSURE_EXPANSION_OUTSIDE_SC"
    "OPE\",\"scope_note\":\"Reports independent pressurized thermal-e"
    "xpansion data too; SVP heat-capacity fit in MAT-SPEC-007 tra"
    "ces earlier Ahlers measurement; not a new SVP calorimetry da"
    "taset\"},{\"doc_id\":\"GASPARINI_MOLDOVER_PRB_1975\",\"document_ki"
    "nd\":\"ORIGINAL_EXPERIMENT_PUBLICATION\",\"campaign\":\"GM75_SVP\","
    "\"lab_family\":\"MINNESOTA_GASPARINI_MOLDOVER\",\"primary_doi\":\"1"
    "0.1103/PhysRevB.12.93\",\"url\":\"https://doi.org/10.1103/PhysRe"
    "vB.12.93\",\"source_bound_measurement_rows\":0,\"per_row_calibra"
    "ted_uncertainty\":false,\"orthogonal_phase_diagnostic\":false,\""
    "condition\":\"PURE_HE4_SVP_SUBSET_NOT_ACQUIRED\",\"scope_note\":\""
    "Original study includes pure helium-4 and 3He-4He mixtures; "
    "no pure-4He source-bound original numeric rows admitted\"},{\""
    "doc_id\":\"GASPARINI_GAETA_PRB_1978\",\"document_kind\":\"REANALYS"
    "IS\",\"campaign\":\"GM75_SVP\",\"lab_family\":\"MINNESOTA_GASPARINI_"
    "MOLDOVER\",\"primary_doi\":\"10.1103/PhysRevB.17.1466\",\"url\":\"ht"
    "tps://doi.org/10.1103/PhysRevB.17.1466\",\"source_bound_measur"
    "ement_rows\":0,\"per_row_calibrated_uncertainty\":false,\"orthog"
    "onal_phase_diagnostic\":false,\"condition\":\"HE4_SVP_FIT_REANAL"
    "YSIS\",\"scope_note\":\"Fit reanalysis of earlier source measure"
    "ments, not a new original SVP calorimeter acquisition\"},{\"do"
    "c_id\":\"STS52_NASA_1994\",\"document_kind\":\"ORIGINAL_EXPERIMENT"
    "_CONFERENCE\",\"campaign\":\"STS52_1992\",\"lab_family\":\"STANFORD_"
    "LIPA\",\"primary_doi\":null,\"url\":\"https://ntrs.nasa.gov/citati"
    "ons/19950007794\",\"source_bound_measurement_rows\":0,\"per_row_"
    "calibrated_uncertainty\":false,\"orthogonal_phase_diagnostic\":"
    "false,\"condition\":\"HE4_LAMBDA_MICROGRAVITY;RUN_LEVEL_CONDITI"
    "ONS_NOT_PINNED\",\"scope_note\":\"1992 orbital experiment confer"
    "ence summary; no primary per-row original data pinned\"},{\"do"
    "c_id\":\"STS52_PRL_1996\",\"document_kind\":\"ORIGINAL_EXPERIMENT_"
    "PUBLICATION\",\"campaign\":\"STS52_1992\",\"lab_family\":\"STANFORD_"
    "LIPA\",\"primary_doi\":\"10.1103/PhysRevLett.76.944\",\"url\":\"http"
    "s://doi.org/10.1103/PhysRevLett.76.944\",\"source_bound_measur"
    "ement_rows\":0,\"per_row_calibrated_uncertainty\":false,\"orthog"
    "onal_phase_diagnostic\":false,\"condition\":\"HE4_LAMBDA_MICROGR"
    "AVITY\",\"scope_note\":\"1996 report of the 1992 orbital experim"
    "ent, not a second orbital acquisition\"},{\"doc_id\":\"STS52_PRB"
    "_2003\",\"document_kind\":\"REVISED_ANALYSIS_SAME_CAMPAIGN\",\"cam"
    "paign\":\"STS52_1992\",\"lab_family\":\"STANFORD_LIPA\",\"primary_do"
    "i\":\"10.1103/PhysRevB.68.174518\",\"url\":\"https://doi.org/10.11"
    "03/PhysRevB.68.174518\",\"source_bound_measurement_rows\":0,\"pe"
    "r_row_calibrated_uncertainty\":false,\"orthogonal_phase_diagno"
    "stic\":false,\"condition\":\"HE4_SVP_MICROGRAVITY\",\"scope_note\":"
    "\"2003 revised analysis of the STS-52 1992 experiment, not a "
    "new acquisition; revised article describes raw experimental "
    "error handling but source rows not pinned\"},{\"doc_id\":\"DONNE"
    "LLY_BARENGHI_1998\",\"document_kind\":\"EVALUATED_COMPILATION\",\""
    "campaign\":null,\"lab_family\":null,\"primary_doi\":\"10.1063/1.55"
    "6028\",\"url\":\"https://doi.org/10.1063/1.556028\",\"source_bound"
    "_measurement_rows\":0,\"per_row_calibrated_uncertainty\":false,"
    "\"orthogonal_phase_diagnostic\":false,\"condition\":\"HE4_SVP_REC"
    "OMMENDED_DATA_NOT_RAW\",\"scope_note\":\"MAT-SPEC-005 evaluated "
    "recommended tables compile older experiments, not an indepen"
    "dently sourced experimental campaign\"},{\"doc_id\":\"BARMATZ_RM"
    "P_2007\",\"document_kind\":\"SECONDARY_FIT_REVIEW\",\"campaign\":nu"
    "ll,\"lab_family\":null,\"primary_doi\":\"10.1103/RevModPhys.79.1\""
    ",\"url\":\"https://doi.org/10.1103/RevModPhys.79.1\",\"source_bou"
    "nd_measurement_rows\":0,\"per_row_calibrated_uncertainty\":fals"
    "e,\"orthogonal_phase_diagnostic\":false,\"condition\":\"HE4_SVP_F"
    "IT_SUMMARIES_NOT_ROW_DATA\",\"scope_note\":\"MAT-SPEC-007 four f"
    "itted parameter records are secondary review values from dis"
    "tinct experiments, not raw row-level measurements\"}],\"noncla"
    "im\":\"A different article or author is not measurement-level "
    "independent reproduction; no per-row errors or independently"
    " measured phase labels are admitted.\"}"
)
EXPECTED_SPEC = json.loads(
    "{\"profile\":\"MAT-SPEC-008\",\"version\":\"0.1.0\",\"parent_profile\""
    ":\"MAT-SPEC-007 v0.1.0\",\"parent_merge_commit\":\"b97348ff8fcf3f"
    "57764dec21a8914f153f96a745\",\"foundational_mat_spec_001_doi\":"
    "\"10.5281/zenodo.24062652\",\"source_catalogue\":\"data/materials"
    "/helium4/mat_spec_008_source_catalogue.json\",\"source_of_nume"
    "rical_rows\":\"MAT-SPEC-006 SHA-pinned original processed Lipa"
    "-Chui table\",\"review_fit_source\":\"MAT-SPEC-007 SHA-pinned se"
    "condary fit table\",\"min_independent_measurement_campaigns\":2"
    ",\"require_source_bound_rows\":true,\"require_measurement_level"
    "_uncertainty\":true,\"require_orthogonal_diagnostic\":true,\"req"
    "uire_lineage_verified_no_shared_run\":true,\"candidate_output\""
    ":\"STRUCTURAL_ONLY_UNAUTHENTICATED at best; never label it em"
    "pirical admission\",\"physical_results\":\"NO_PHASE_CLASSIFIER_N"
    "O_HOLDOUT_ACCURACY_NO_RAW_INDEPENDENT_REPLICATION\",\"runtime_"
    "artifacts\":\"canonical JSON/CSV symbolic evidence only, no au"
    "dio PCM WAV MIDI playback\",\"future\":\"MAT-SPEC-009 only if th"
    "is gate admits adequate independent campaigns; MAT-SPEC-010 "
    "closes numbered series; SPARK/Ada and Lean/ECMA after 010\"}"
)
