"""MAT-SPEC-007: independent experiment-lineage fit concordance audit.

SPDX-License-Identifier: MPL-2.0
Copyright (c) 2026 Trent Slade / QSOL-IMC.

Review-derived fitted summaries are NOT original instrument measurements.
No physical phase classifier, p-value, or sampled audio is generated.
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

from materials import mat_spec, mat_spec_006

PROFILE = "MAT-SPEC-007"
VERSION = "0.1.0"
PARENT_COMMIT = "c1abb62e8914f6790b5da5a51adf330b813b0530"
FOUNDATIONAL_DOI = "10.5281/zenodo.24062652"
SOURCE_PATH = "data/materials/helium4/mat_spec_007_svp_fit_summaries.csv"
META_PATH = "data/materials/helium4/mat_spec_007_svp_fit_summaries.source.json"
SPEC_PATH = "spec/mat-spec-007.v0.1.json"
SOURCE_SHA256 = "b3457eeafd8bda8f8b9ebd63d4cd72af825fd8bd04e2660d01f637578db79489"
OUTPUT_NAMES = frozenset({
    "contract.json", "fit-summaries.csv", "pair-relations.csv",
    "lineage.json", "receiver.json", "replication-gate.json",
    "audit.json", "manifest.json",
})
IMPLEMENTATION_PATHS = ("materials/mat_spec_007.py", "scripts/build_mat_spec_007.py")
RECORD_IDS = (
    "AHLERS_1971", "GASPARINI_MOLDOVER_1975",
    "LIPA_CHUI_1983", "LIPA_STS52_1992",
)
FIELDS = (
    "record_id", "acquisition_campaign", "lab_family",
    "measurement_doi", "analysis_doi", "alpha", "alpha_reported_error",
    "amplitude_ratio", "amplitude_ratio_reported_error",
    "reference_condition", "provenance_note",
)
# Frozen seven-output MAT-SPEC-006 baseline from merged-main CI.
PARENT_V6_SHA256 = {
    "contract.json": "7123827c61661ff778f5b71a549063498993e34dd9dae83835b1d945b4aa7fdd",
    "heldout.json": "7d14cdee77ece859979f3dec8aab88458a7db2992e89f804ecf55888beb32e45",
    "manifest.json": "ad28104ad2633c95f30130724d2c1f48652701305fc9615c0e29f90b23424d27",
    "observations.json": "140f954eb82879196af55c6e374d27b3ec40fbfee889566781fcf49737706bca",
    "phase-gate.json": "dc25fe60243e178808b6e6fb3ff7bce02c5d7a9b6cfd01108147227b19e5e319",
    "receiver-controls.csv": "1e1587ab1570969737905adf0d1cc8c2448371f9d4f6bf276e4feec8218e25fc",
    "source-audit.json": "43bbba20e41360cbc859d9d324cbc2a3517e83557f40928816c13285f29ab623",
}

EXPECTED_META = json.loads(
    "{\"profile\":\"MAT-SPEC-007\",\"version\":\"0.1.0\",\"review_title\":\""
    "Critical phenomena in microgravity: Past, present, and futur"
    "e\",\"review_doi\":\"10.1103/RevModPhys.79.1\",\"review_table\":\"Ta"
    "ble VII, asterisked SVP entries\",\"review_authors\":[\"M. Barma"
    "tz\",\"Inseob Hahn\",\"J. A. Lipa\",\"R. V. Duncan\"],\"review_url\":"
    "\"https://www.depts.ttu.edu/phas/cees/Projects/Images_And_pdf"
    "s/Barmatz_RMP_2007.pdf\",\"data_kind\":\"four secondary publishe"
    "d fit summaries, not raw experimental measurements\",\"origina"
    "l_experiments\":[{\"record_id\":\"AHLERS_1971\",\"original_doi\":\"1"
    "0.1103/PhysRevA.3.696\",\"analysis_doi\":\"10.1103/PhysRevB.14.2"
    "096\",\"acquisition_campaign\":\"AL71_SVP\",\"lab_family\":\"BELL_AH"
    "LERS\",\"note\":\"Mueller et al 1976 re-fit original Ahlers 1971"
    " data, not a new 1976 SVP measurement\"},{\"record_id\":\"GASPAR"
    "INI_MOLDOVER_1975\",\"original_doi\":\"10.1103/PhysRevB.12.93\",\""
    "analysis_doi\":\"10.1103/PhysRevB.17.1466\",\"acquisition_campai"
    "gn\":\"GM75_SVP\",\"lab_family\":\"MINNESOTA_GASPARINI_MOLDOVER\",\""
    "note\":\"Gasparini Gaeta 1978 reanalysis of the Gasparini Mold"
    "over 1975 pure helium 4 measurement\"},{\"record_id\":\"LIPA_CHU"
    "I_1983\",\"original_doi\":\"10.1103/PhysRevLett.51.2291\",\"analys"
    "is_doi\":\"10.1103/PhysRevLett.51.2291\",\"acquisition_campaign\""
    ":\"LC83_SVP\",\"lab_family\":\"STANFORD_LIPA\",\"note\":\"Original 19"
    "83 ground experiment also reported in MAT-SPEC-006 NASA appe"
    "ndix\"},{\"record_id\":\"LIPA_STS52_1992\",\"original_doi\":\"10.110"
    "3/PhysRevLett.76.944\",\"analysis_doi\":\"10.1103/PhysRevB.68.17"
    "4518\",\"acquisition_campaign\":\"STS52_1992\",\"lab_family\":\"STAN"
    "FORD_LIPA\",\"note\":\"1992 orbital experiment described in 1996"
    " and revised in 2003, not two campaigns\"}],\"scope\":\"pure hel"
    "ium-4 at saturated vapour pressure; derived critical alpha a"
    "nd Aplus/Aminus fits\",\"uncertainty\":\"parenthetical uncertain"
    "ties converted to decimals; unknown common confidence interp"
    "retation, covariance and fitted-model comparability\",\"lineag"
    "e\":\"4 acquisition campaigns, 3 laboratory families, 1 review"
    " compilation; raw experimental record independence not indep"
    "endently audited\",\"data_sha256\":\"b3457eeafd8bda8f8b9ebd63d4c"
    "d72af825fd8bd04e2660d01f637578db79489\",\"rights\":\"small selec"
    "tion of attributed factual numeric fit values; no review PDF"
    " redistributed\"}"
)
EXPECTED_SPEC = json.loads(
    "{\"profile\":\"MAT-SPEC-007\",\"version\":\"0.1.0\",\"parent_profile\""
    ":\"MAT-SPEC-006 v0.1.0\",\"parent_commit\":\"c1abb62e8914f6790b5d"
    "a5a51adf330b813b0530\",\"mat_spec_001_record_doi\":\"10.5281/zen"
    "odo.24062652\",\"review_doi\":\"10.1103/RevModPhys.79.1\",\"data_s"
    "ha256\":\"b3457eeafd8bda8f8b9ebd63d4cd72af825fd8bd04e2660d01f6"
    "37578db79489\",\"sources\":\"4 asterisked pure helium-4 SVP fit "
    "summary rows from review Table VII\",\"numerics\":\"Fraction exa"
    "ct closed reported-fit-uncertainty boxes, touching overlaps\""
    ",\"comparison\":\"6 distinct campaign pairs, 3 lab-family group"
    "s, unknown cross-fit covariance\",\"receiver\":\"400 Hz per dime"
    "nsionless Aplus/Aminus ratio to 12-TET note; signed alpha no"
    "t pitched\",\"claim\":\"compare published fits, not raw experime"
    "ntal measurements, verified phase diagnoses, or a phase clas"
    "sifier\",\"experimental_independence\":\"different acquisition o"
    "rigin from independent papers; shared review and some author"
    "s; not an authenticated heldout run\",\"outputs\":\"canonical JS"
    "ON and CSV only; root PCM/WAV generation prohibited\",\"closur"
    "e\":\"MAT-SPEC-010 is final; thereafter SPARK/Ada and VANILLAJ"
    "S Lean-ECMAScript refinement\"}"
)


def decimal(text: str, *, positive: bool = False) -> Fraction:
    if not isinstance(text, str) or not re.fullmatch(
        r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", text
    ):
        raise ValueError("invalid reported fit decimal")
    value = Fraction(text)
    if positive and value <= 0:
        raise ValueError("expected positive reported fit or error")
    return value


def parse_source(raw: bytes) -> list[dict]:
    """Require one exact review transcription, no extra rows or columns."""
    if mat_spec.sha256(raw) != SOURCE_SHA256:
        raise ValueError("source fit SHA-256 mismatch")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("ascii")), strict=True)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError("invalid published fit columns")
        rows = list(reader)
    except (UnicodeError, csv.Error) as exc:
        raise ValueError("invalid published fit CSV") from exc
    if (
        len(rows) != 4
        or tuple(r.get("record_id") for r in rows) != RECORD_IDS
        or any(None in r or None in r.values() for r in rows)
    ):
        raise ValueError("published fit excerpt membership mismatch")
    for row, origin in zip(rows, EXPECTED_META["original_experiments"], strict=True):
        if (
            row["reference_condition"] != "HE4_SVP"
            or row["acquisition_campaign"] != origin["acquisition_campaign"]
            or row["lab_family"] != origin["lab_family"]
            or row["measurement_doi"] != origin["original_doi"]
            or row["analysis_doi"] != origin["analysis_doi"]
            or decimal(row["alpha"]) >= 0
        ):
            raise ValueError("measurement/analysis source family or domain drift")
        for field in ("alpha_reported_error", "amplitude_ratio",
                      "amplitude_ratio_reported_error"):
            decimal(row[field], positive=True)
    return rows


def interval(row: dict, field: str) -> tuple[Fraction, Fraction]:
    if field not in {"alpha", "amplitude_ratio"}:
        raise ValueError("unexpected fitted quantity")
    center = decimal(row[field])
    err = decimal(row[field + "_reported_error"], positive=True)
    return center - err, center + err


def classify(a: tuple[Fraction, Fraction], b: tuple[Fraction, Fraction]) -> str:
    if a[0] > a[1] or b[0] > b[1]:
        raise ValueError("invalid reported-fit interval")
    if a[1] < b[0]:
        return "a_below_b"
    if b[1] < a[0]:
        return "b_below_a"
    return "overlap"


def pairwise_fits(rows: list[dict]) -> tuple[list[dict], dict]:
    if tuple(x["record_id"] for x in rows) != RECORD_IDS:
        raise ValueError("unexpected fit order")
    pairs = []
    counts = {
        prop: {"a_below_b": 0, "b_below_a": 0, "overlap": 0}
        for prop in ("alpha", "amplitude_ratio")
    }
    reverse = {
        "a_below_b": "b_below_a", "b_below_a": "a_below_b", "overlap": "overlap"
    }
    for a, b in combinations(rows, 2):
        if a["acquisition_campaign"] == b["acquisition_campaign"]:
            raise ValueError("same campaign counted as independent")
        entry = {
            "record_a": a["record_id"], "record_b": b["record_id"],
            "different_campaign": True,
            "different_lab_family": a["lab_family"] != b["lab_family"],
            "review_is_shared": True,
        }
        for prop in counts:
            left, right = interval(a, prop), interval(b, prop)
            relation = classify(left, right)
            if reverse[classify(right, left)] != relation:
                raise ValueError("pressure-order reversal covariance failed")
            doubled = ((2 * left[0], 2 * left[1]),
                       (2 * right[0], 2 * right[1]))
            if classify(*doubled) != relation:
                raise ValueError("positive scale covariance failed")
            entry[prop + "_relation"] = relation
            counts[prop][relation] += 1
        pairs.append(entry)
    if len(pairs) != 6 or any(sum(x.values()) != 6 for x in counts.values()):
        raise ValueError("fit comparison conservation failed")
    return pairs, {
        "relations": counts,
        "distinct_acquisition_campaign_pairs": 6,
        "cross_lab_family_pairs": sum(p["different_lab_family"] for p in pairs),
        "same_lab_distinct_campaign_pairs": sum(
            not p["different_lab_family"] for p in pairs
        ),
        "statistical_significance": "NOT_TESTED",
        "source_reviewer_independence": "NOT_ESTABLISHED",
    }


def receiver_audit(rows: list[dict]) -> dict:
    """One dimensionless positive receiver; negative alpha stays unpitched."""
    profiles = []
    for row in rows:
        target = 400 * decimal(row["amplitude_ratio"], positive=True)
        profiles.append({
            "record_id": row["record_id"],
            "exact_ratio": row["amplitude_ratio"],
            "authored_target_Hz": str(target),
            "nearest_midi_note": mat_spec.nearest_midi(target),
        })
    if any(
        Fraction(p["authored_target_Hz"]) / 400 != Fraction(p["exact_ratio"])
        for p in profiles
    ):
        raise ValueError("exact ratio roundtrip failed")
    notes = [p["nearest_midi_note"] for p in profiles]
    return {
        "profiles": profiles,
        "exact_ratio_count": len({p["exact_ratio"] for p in profiles}),
        "midi_note_count": len(set(notes)),
        "midi_colliding_pairs": sum(a == b for a, b in combinations(notes, 2)),
        "alpha_signed_exponent_not_pitched": True,
        "nominal_only": True,
        "listener_test": "NOT_PERFORMED",
        "scale": "authored 400 Hz per dimensionless Aplus/Aminus unit",
    }


def gate(rows: list[dict], counts: dict) -> dict:
    origins = EXPECTED_META["original_experiments"]
    if (
        len({r["acquisition_campaign"] for r in rows}) != 4
        or len({r["lab_family"] for r in rows}) != 3
        or tuple(o["record_id"] for o in origins) != RECORD_IDS
    ):
        raise ValueError("invalid independent campaign lineage")
    return {
        "status": "PUBLISHED_FIT_CONCORDANCE_ONLY",
        "separate_experiment_campaign_origins": 4,
        "distinct_lab_families": 3,
        "fit_review_compilations": 1,
        "alpha_reported_box_relations": counts["relations"]["alpha"],
        "ratio_reported_box_relations": counts["relations"]["amplitude_ratio"],
        "result": "MIXED_OVERLAP_AND_SEPARATION",
        "raw_experiment_independence_attested": False,
        "raw_measurement_replication": "NOT_PERFORMED",
        "phase_classifier_training": "NOT_PERFORMED",
        "phase_classifier_heldout_score": None,
        "uncertainty_scope": "UNHARMONIZED_REPORTED_FIT_ERRORS_NO_COVARIANCE",
        "requirements_open": [
            "NO_RAW_CAMPAIGN_DATA_REPLAY",
            "REVIEW_TABLE_NOT_INDEPENDENT_BLIND_VALIDATION",
            "REANALYSES_NOT_NEW_EXPERIMENT_CAMPAIGNS",
            "NO_INDEPENDENT_PHASE_DIAGNOSTIC_LABELS",
            "NO_SOURCE_SEPARATED_HOLDOUT_OR_HARMONIZED_FIT_ERRORS",
        ],
        "no_lean_ada_or_e8_claim": True,
    }


def table_bytes(rows: list[dict]) -> bytes:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("ascii")


def build_evidence(root: Path) -> dict[str, bytes]:
    parent = mat_spec_006.build_evidence(root)
    if set(parent) != mat_spec_006.OUTPUT_NAMES:
        raise ValueError("MAT-SPEC-006 parent artifact membership drift")
    parent_hashes = {name: mat_spec.sha256(raw) for name, raw in parent.items()}
    if PARENT_V6_SHA256 is not None and parent_hashes != PARENT_V6_SHA256:
        raise ValueError("frozen MAT-SPEC-006 parent digest drift")
    parent_receipt = json.loads(parent["manifest.json"])
    if (
        parent_receipt.get("profile") != "MAT-SPEC-006"
        or parent_receipt.get("version") != "0.1.0"
        or parent_receipt.get("parent", {}).get("commit") != mat_spec_006.PARENT_COMMIT
        or parent_receipt.get("parent", {}).get("foundational_doi") != FOUNDATIONAL_DOI
    ):
        raise ValueError("MAT-SPEC-006 parent identity mismatch")
    if any(
        mat_spec.sha256(parent[name]) != rec["sha256"]
        for name, rec in parent_receipt["outputs"].items()
    ):
        raise ValueError("MAT-SPEC-006 parent output receipt inconsistency")
    raw = mat_spec.read_regular(root / SOURCE_PATH)
    meta_raw = mat_spec.read_regular(root / META_PATH)
    spec_raw = mat_spec.read_regular(root / SPEC_PATH)
    if json.loads(meta_raw) != EXPECTED_META or json.loads(spec_raw) != EXPECTED_SPEC:
        raise ValueError("frozen review lineage or profile specification drift")
    rows = parse_source(raw)
    pairs, audit = pairwise_fits(rows)
    receiver = receiver_audit(rows)
    decision = gate(rows, audit)
    products = {
        "contract.json": mat_spec.canonical_json(EXPECTED_SPEC),
        "fit-summaries.csv": table_bytes(rows),
        "pair-relations.csv": table_bytes(pairs),
        "lineage.json": mat_spec.canonical_json(EXPECTED_META),
        "receiver.json": mat_spec.canonical_json(receiver),
        "replication-gate.json": mat_spec.canonical_json(decision),
        "audit.json": mat_spec.canonical_json({
            "profile": PROFILE, "version": VERSION,
            "rows": len(rows), "compared_campaign_pairs": len(pairs),
            "pair_audit": audit, "source_is_secondary_review_summary": True,
            "audio_generated": False,
        }),
    }
    implementation = {
        path: mat_spec.sha256(mat_spec.read_regular(root / path))
        for path in IMPLEMENTATION_PATHS
    }
    manifest = {
        "profile": PROFILE, "version": VERSION,
        "parent_commit": PARENT_COMMIT,
        "parent_artifacts": {
            name: {"sha256": digest, "bytes": len(parent[name])}
            for name, digest in sorted(parent_hashes.items())
        },
        "source": {
            "path": SOURCE_PATH, "sha256": mat_spec.sha256(raw),
            "bytes": len(raw), "review_doi": EXPECTED_META["review_doi"],
        },
        "metadata": {"path": META_PATH, "sha256": mat_spec.sha256(meta_raw)},
        "contract": {"path": SPEC_PATH, "sha256": mat_spec.sha256(spec_raw)},
        "implementation": implementation,
        "outputs": {
            name: {"sha256": mat_spec.sha256(raw), "bytes": len(raw)}
            for name, raw in sorted(products.items())
        },
        "foundational_mat_spec_001_doi": FOUNDATIONAL_DOI,
        "serialization": "ASCII sorted JSON LF and CSV LF",
        "manifest_self_hash": None, "canonical_pcm_sha256": None,
        "canonical_wav_sha256": None, "audio_generated": False,
    }
    products["manifest.json"] = mat_spec.canonical_json(manifest)
    return products


def write_evidence(root: Path, destination: str, products: dict[str, bytes]) -> Path:
    """POSIX no-follow anchored and exclusive symbolic-only output."""
    path = PurePosixPath(destination)
    if (
        not destination or path.is_absolute() or "\\" in destination
        or any(part in {"", ".", ".."} for part in destination.split("/"))
    ):
        raise ValueError("invalid output destination")
    if set(products) != OUTPUT_NAMES or any(
        PurePosixPath(name).name != name
        or Path(name).suffix not in {".csv", ".json"} for name in products
    ):
        raise ValueError("disallowed output membership or extension")
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
            with os.fdopen(fd, "wb") as h:
                h.write(products[name])
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
