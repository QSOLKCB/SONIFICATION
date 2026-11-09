"""MAT-SPEC-004: exact temperature-parameter preservation and phase evidence gate.

SPDX-License-Identifier: MPL-2.0
Copyright (c) 2026 Trent Slade / QSOL-IMC.

The source is a published MODEL-INPUT TABLE, not an independent measurement
campaign or phase-labelled temperature series. No sound samples are generated.
"""
from __future__ import annotations

import csv
import io
import json
import os
import stat
from contextlib import suppress
from fractions import Fraction
from itertools import combinations
from pathlib import Path, PurePosixPath

from materials import mat_spec, mat_spec_002, mat_spec_003

PROFILE = "MAT-SPEC-004"
VERSION = "0.1.0"
PARENT_COMMIT = "c15ef3223e78cffad1494d99ad6edbdb41195362"
RELATED_DOI = "10.5281/zenodo.24062652"
SOURCE_DOI = "10.1063/5.0083847"
DATA_PATH = "data/materials/helium4/temperature_table1_2022.csv"
META_PATH = "data/materials/helium4/temperature_table1_2022.source.json"
SPEC_PATH = "spec/mat-spec-004.v0.1.json"
DATA_SHA256 = "e741aac11809d18d05451efd30ca96dba0ae98765bde4952b0af96daeef8cf82"
EXPECTED_TEMPERATURES = ("0.9", "1.1", "1.2", "1.4", "1.6", "1.8", "1.9", "2.1")
EXPECTED_HEADERS = ("temperature_K", "normal_fraction", "mutual_friction_alpha")
IMPLEMENTATION_PATHS = (
    "materials/mat_spec_004.py", "scripts/build_mat_spec_004.py",
)
OUTPUT_NAMES = frozenset({
    "contract.json", "observations.json", "temperature-controls.csv",
    "audit.json", "phase-gate.json", "manifest.json",
})
# Populate from a CI replay on the merged MAT-SPEC-003 main commit, then
# fail closed on all eight fixed output identities before review.
PARENT_V3_SHA256: dict[str, str] | None = None

EXPECTED_META = {
    "authors": ["Abhiroop Bhadra", "Pankaj Kumar Mishra"],
    "source_doi": SOURCE_DOI,
    "source_title": (
        "Energy spectrum and energy budget of superfluid turbulence "
        "using two-fluid shell model"
    ),
    "source_journal": "AIP Advances 12, 025021 (2022)",
    "table": "Table I: Parameters for superfluid helium-4 at different temperatures",
    "url": "https://doi.org/10.1063/5.0083847",
    "licence": "CC BY 4.0 (source article; numerical transcriptions attributed)",
    "data_kind": (
        "eight published parameter-table entries used in a two-fluid "
        "shell-model study; not raw measurements"
    ),
    "temperature_units": "K",
    "normal_fraction_units": "dimensionless rho_n/rho",
    "mutual_friction_alpha_units": "dimensionless",
    "fraction_uncertainty": "not reported in Table I",
    "phase_diagnostic": "not supplied in Table I",
    "pressure_condition": (
        "not independently specified for these table entries; do not assert SVP"
    ),
    "comparison_to_mat_spec_003": (
        "different temperature/pressure scope; cross-profile physical matching prohibited"
    ),
    "provenance_note": (
        "The numerical source is distinct from the Godfrin et al. helium "
        "dispersion table used in MAT-SPEC-001/003."
    ),
}
EXPECTED_SPEC = {
    "profile": PROFILE,
    "version": VERSION,
    "title": "Helium temperature-series preservation and phase-evidence admission",
    "parent_profile": "MAT-SPEC-003 v0.1.0",
    "parent_commit": PARENT_COMMIT,
    "parent_mat_spec_001_doi": RELATED_DOI,
    "source_doi": SOURCE_DOI,
    "source_sha256": DATA_SHA256,
    "source_rows": 8,
    "source_scope": (
        "eight distinct below-transition helium-II simulation-parameter inputs, "
        "not primary phase measurements"
    ),
    "fraction_rule": "exact rational superfluid_fraction = 1 - reported normal_fraction",
    "receiver_rule": (
        "authored 400 Hz * superfluid_fraction; symbolic nearest 12-TET and dense ranks"
    ),
    "receiver_unit": "Hz for an authored control target; not a measured acoustic signal",
    "uncertainty_rule": "not reported, encode as null; never assume zero",
    "phase_evidence_rule": (
        "blocked without independently measured above/below transition diagnostics, "
        "calibrated errors and a source-separated held-out test"
    ),
    "output_rule": "symbolic canonical JSON and CSV only; no MIDI/audio rendered",
    "source_licence": "CC BY 4.0",
    "code_licence": "MPL-2.0",
}


def _field_fraction(value: str, *, maximum: Fraction | None = None) -> Fraction:
    """Strict decimal string parser: no NaN, negative, exponent or whitespace."""
    if (
        not value or value.strip() != value
        or any(ch not in "0123456789." for ch in value)
        or value.count(".") > 1 or value.startswith(".") or value.endswith(".")
    ):
        raise ValueError("invalid published decimal representation")
    number = Fraction(value)
    if number < 0 or (maximum is not None and number > maximum):
        raise ValueError("physical parameter outside declared range")
    return number


def parse_source(source_bytes: bytes) -> list[dict]:
    """Reject byte drift and parse only the attributed 2022 Table I excerpt."""
    if mat_spec.sha256(source_bytes) != DATA_SHA256:
        raise ValueError("temperature source SHA-256 mismatch")
    rows = list(csv.reader(io.StringIO(source_bytes.decode("ascii")), strict=True))
    if (
        len(rows) != 9
        or tuple(rows[0]) != EXPECTED_HEADERS
        or any(len(row) != 3 for row in rows)
        or tuple(row[0] for row in rows[1:]) != EXPECTED_TEMPERATURES
    ):
        raise ValueError("unexpected temperature-series layout")
    observations = []
    for temperature, normal_text, alpha_text in rows[1:]:
        normal = _field_fraction(normal_text, maximum=Fraction(1))
        alpha = _field_fraction(alpha_text)
        t = _field_fraction(temperature)
        if t <= 0 or alpha > 1:
            raise ValueError("invalid temperature or alpha")
        superfluid = 1 - normal
        observations.append({
            "temperature_K": temperature,
            "normal_fraction": normal_text,
            "mutual_friction_alpha": alpha_text,
            "superfluid_fraction": str(superfluid),
            "superfluid_fraction_uncertainty": None,
            "source_phase_scope": "HE_II_MODEL_PARAMETER",
            "independent_phase_label": None,
            "independent_phase_diagnostic": None,
            "source_is_raw_measurement": False,
            "source_doi": SOURCE_DOI,
        })
    return observations


def is_strictly_decreasing(values: list[Fraction]) -> bool:
    return all(a > b for a, b in zip(values, values[1:], strict=False))


def map_temperature(rows: list[dict]) -> list[dict]:
    if len(rows) != 8:
        raise ValueError("expected exactly eight temperature samples")
    fractions = [Fraction(row["superfluid_fraction"]) for row in rows]
    ranks = mat_spec.rank_offsets(fractions)
    mapped = []
    for index, (item, fraction, rank) in enumerate(
        zip(rows, fractions, ranks, strict=True)
    ):
        if not 0 <= fraction <= 1:
            raise ValueError("invalid derived superfluid fraction")
        if fraction + Fraction(item["normal_fraction"]) != 1:
            raise ValueError("two-fluid mass-fraction closure failed")
        frequency = 400 * fraction
        note = mat_spec.nearest_midi(frequency)
        mapped.append({
            **item,
            "sample_index": index,
            "frequency_target_Hz": str(frequency),
            "quantized_midi_note": note,
            "quantization_error_cents": (
                None if note is None else mat_spec.cents_error(frequency, note)
            ),
            "rank_offset": rank,
        })
    return mapped


def phase_admission(rows: list[dict]) -> dict:
    """Evidence gate: refuse labels/phase inference from a single-regime table.

    Not a trainable or tunable classifier. Caller-supplied labels do not turn
    an unattributed source into an independently validated diagnostic.
    """
    all_source_only = all(
        row["source_phase_scope"] == "HE_II_MODEL_PARAMETER"
        and row["independent_phase_label"] is None
        and row["independent_phase_diagnostic"] is None
        and row["source_is_raw_measurement"] is False
        for row in rows
    )
    if not all_source_only or len(rows) != 8:
        raise ValueError("unrecognised phase evidence or altered source scope")
    return {
        "status": "BLOCKED_INSUFFICIENT_PHYSICAL_EVIDENCE",
        "phase_classifier_trained": False,
        "holdout_score": None,
        "phase_accuracy": None,
        "independent_blinded_listener_result": None,
        "observed_regimes": {"source_described_He_II": 8, "verified_He_I": 0},
        "reasons": [
            "NO_INDEPENDENT_NORMAL_HELIUM_OBSERVATIONS",
            "NO_INDEPENDENT_PHASE_DIAGNOSTIC",
            "SOURCE_TABLE_REPORTS_NO_PER_ROW_UNCERTAINTY",
            "NO_SOURCE_SEPARATED_HELD_OUT_TEST",
            "SOURCE_ENTRIES_ARE_MODEL_PARAMETERS_NOT_RAW_MEASUREMENTS",
        ],
        "admission_rule": (
            "Do not admit phase discrimination without independently attributed "
            "He-I/He-II observations, diagnostics, uncertainty and held-out evidence."
        ),
        "contextual_lambda_point_K": "2.1768",
        "lambda_context_source": "Donnelly and Barenghi 1998; saturated vapour pressure only",
        "temperature_threshold_used_as_classifier": False,
        "same_conditions_as_Godfrin_pressure_series": False,
        "no_e8_or_theory_of_everything_claim": True,
    }


def audit_temperature(mapped: list[dict]) -> dict:
    exact = 0
    percentages = []
    notes = []
    for item in mapped:
        fraction = Fraction(item["superfluid_fraction"])
        normal = Fraction(item["normal_fraction"])
        frequency = Fraction(item["frequency_target_Hz"])
        if fraction + normal != 1 or frequency / 400 != fraction:
            raise ValueError("fraction closure or frequency roundtrip failed")
        exact += 1
        percentages.append(fraction)
        notes.append(item["quantized_midi_note"])
    if not is_strictly_decreasing(percentages):
        raise ValueError("reported reference fraction is not strictly decreasing")
    if is_strictly_decreasing(list(reversed(percentages))):
        raise ValueError("negative reassociation control failed")
    pair_collisions = sum(a == b for a, b in combinations(notes, 2))
    distinct = len(set(notes))
    if distinct + pair_collisions > len(mapped) + len(mapped) * (len(mapped) - 1) // 2:
        raise ValueError("invalid receiver counts")
    return {
        "profile": PROFILE,
        "version": VERSION,
        "source_entries": len(mapped),
        "exact_mass_fraction_closure_checks": exact,
        "exact_authored_frequency_roundtrips": exact,
        "source_table_monotonic_temperature_fraction": True,
        "reverse_reassociation_negative_control": "PASS",
        "no_reported_fraction_uncertainties": True,
        "full_precision_fraction_values_distinct": len(set(percentages)),
        "quantized_midi_unique_notes": distinct,
        "quantized_midi_colliding_pairs": pair_collisions,
        "pairwise_source_comparisons": len(mapped) * (len(mapped) - 1) // 2,
        "physical_meaning": (
            "descriptive model-parameter table; no independently observed "
            "transition, phase classification or listener test"
        ),
        "audio_generated": False,
    }


def _control_csv(mapped: list[dict]) -> bytes:
    keys = (
        "sample_index", "temperature_K", "normal_fraction",
        "superfluid_fraction", "mutual_friction_alpha",
        "superfluid_fraction_uncertainty", "frequency_target_Hz",
        "quantized_midi_note", "quantization_error_cents", "rank_offset",
    )
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=keys, lineterminator="\n")
    writer.writeheader()
    for item in mapped:
        writer.writerow({key: item[key] for key in keys})
    return out.getvalue().encode("ascii")


def build_evidence(root: Path) -> dict[str, bytes]:
    """Rebuild parents, enforce known source identity and emit symbolic outputs."""
    parent = mat_spec_003.build_evidence(root)
    receipts = {key: mat_spec.sha256(data) for key, data in parent.items()}
    if PARENT_V3_SHA256 is not None and receipts != PARENT_V3_SHA256:
        raise ValueError("frozen MAT-SPEC-003 parent SHA-256 mismatch")
    parent_manifest = json.loads(parent["manifest.json"])
    if (
        parent_manifest.get("profile") != "MAT-SPEC-003"
        or parent_manifest.get("version") != "0.1.0"
        or parent_manifest.get("related_doi") != RELATED_DOI
    ):
        raise ValueError("invalid MAT-SPEC-003 ancestor")
    for name, receipt in parent_manifest["outputs"].items():
        if name not in parent or mat_spec.sha256(parent[name]) != receipt["sha256"]:
            raise ValueError("parent output receipt inconsistent")

    source = mat_spec.read_regular(root / DATA_PATH)
    metadata_bytes = mat_spec.read_regular(root / META_PATH)
    spec_bytes = mat_spec.read_regular(root / SPEC_PATH)
    metadata = json.loads(metadata_bytes)
    spec = json.loads(spec_bytes)
    if metadata != EXPECTED_META or spec != EXPECTED_SPEC:
        raise ValueError("MAT-SPEC-004 source provenance or contract drift")
    if source != source.encode("ascii").decode("ascii").encode("ascii"):
        raise ValueError("unexpected source encoding")
    observations = parse_source(source)
    mapped = map_temperature(observations)
    audit = audit_temperature(mapped)
    gate = phase_admission(observations)
    products = {
        "contract.json": mat_spec.canonical_json(spec),
        "observations.json": mat_spec.canonical_json({
            "source": metadata, "observations": observations
        }),
        "temperature-controls.csv": _control_csv(mapped),
        "audit.json": mat_spec.canonical_json(audit),
        "phase-gate.json": mat_spec.canonical_json(gate),
    }
    implementation = {
        path: mat_spec.sha256(mat_spec.read_regular(root / path))
        for path in IMPLEMENTATION_PATHS
    }
    manifest = {
        "profile": PROFILE, "version": VERSION,
        "parent_commit": PARENT_COMMIT,
        "parent_artifacts": {
            key: {"sha256": value, "bytes": len(parent[key])}
            for key, value in sorted(receipts.items())
        },
        "parent_mat_spec_001_doi": RELATED_DOI,
        "source": {
            "doi": SOURCE_DOI, "table": "Table I",
            "path": DATA_PATH, "sha256": mat_spec.sha256(source),
            "bytes": len(source),
            "kind": "attributed secondary model-input table, not raw measurements",
        },
        "source_metadata": {
            "path": META_PATH,
            "sha256": mat_spec.sha256(metadata_bytes),
        },
        "contract_input": {
            "path": SPEC_PATH, "sha256": mat_spec.sha256(spec_bytes),
        },
        "implementation": implementation,
        "outputs": {
            name: {"sha256": mat_spec.sha256(data), "bytes": len(data)}
            for name, data in sorted(products.items())
        },
        "canonical": "sorted ASCII JSON LF; CSV LF; no clocks or paths in output receipts",
        "manifest_self_hash": None,
        "canonical_pcm_sha256": None,
        "canonical_wav_sha256": None,
        "audio_generated": False,
    }
    products["manifest.json"] = mat_spec.canonical_json(manifest)
    return products


def write_evidence(root: Path, destination: str, artifacts: dict[str, bytes]) -> Path:
    """Fail-closed symbolic allowlist, anchored directory FDs, no overwrite."""
    path = PurePosixPath(destination)
    if (
        not destination or path.is_absolute() or "\\" in destination
        or any(part in {"", ".", ".."} for part in destination.split("/"))
    ):
        raise ValueError("invalid output destination")
    if set(artifacts) != OUTPUT_NAMES or any(
        PurePosixPath(name).name != name
        or Path(name).suffix not in {".csv", ".json"} for name in artifacts
    ):
        raise ValueError("only declared symbolic artifacts are allowed")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fds = [os.open(root, flags)]
    try:
        for component in path.parts[:-1]:
            with suppress(FileExistsError):
                os.mkdir(component, mode=0o755, dir_fd=fds[-1])
            fds.append(os.open(component, flags, dir_fd=fds[-1]))
        parent = fds[-1]
        os.mkdir(path.parts[-1], mode=0o755, dir_fd=parent)
        fds.append(os.open(path.parts[-1], flags, dir_fd=parent))
        out = fds[-1]
        for name in sorted(artifacts):
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode=0o644, dir_fd=out,
            )
            with os.fdopen(fd, "wb") as stream:
                stream.write(artifacts[name])
        opened = os.fstat(out)
        visible = os.stat(path.parts[-1], dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISDIR(visible.st_mode) or (
            opened.st_dev, opened.st_ino
        ) != (visible.st_dev, visible.st_ino):
            raise ValueError("destination was replaced during writing")
    finally:
        for fd in reversed(fds):
            os.close(fd)
    return root / path
