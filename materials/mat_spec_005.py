"""MAT-SPEC-005: source-bound two-sided helium lambda reference and witness gate.

SPDX-License-Identifier: MPL-2.0
Copyright (c) 2026 Trent Slade / QSOL-IMC.

Experiment-derived RECOMMENDED TABLES are not raw measured trials. No PCM/audio.
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

from materials import mat_spec, mat_spec_004

PROFILE = "MAT-SPEC-005"
VERSION = "0.1.0"
PARENT_COMMIT = "eac0659cbae1392bf63632ec8138005367e63304"
FOUNDATIONAL_DOI = "10.5281/zenodo.24062652"
SOURCE_DOI = "10.1063/1.556028"
DATA_PATH = "data/materials/helium4/nist_svp_lambda_reference_1998.csv"
META_PATH = "data/materials/helium4/nist_svp_lambda_reference_1998.source.json"
SPEC_PATH = "spec/mat-spec-005.v0.1.json"
DATA_SHA256 = "e39c29c8dab12a789d6a80d86487c61a4b25c53b68a58d83a88f03bb66755b8e"
LAMBDA = Fraction("2.1768")
SELECTED_T = (
    "2.1500", "2.1760", "2.1761", "2.1762", "2.1763", "2.1764",
    "2.1765", "2.1766", "2.1767", "2.1768", "2.1769", "2.1770",
    "2.1800", "2.2000",
)
COLUMN_NAMES = (
    "temperature_K", "first_sound_m_per_s", "second_sound_m_per_s",
    "heat_capacity_J_per_mol_K",
)
SCALES = {
    "first_sound_m_per_s": Fraction(2),
    "second_sound_m_per_s": Fraction(40),
    "heat_capacity_J_per_mol_K": Fraction(16),
}
SOURCE_PROPERTIES = tuple(SCALES)
OUTPUT_NAMES = frozenset({
    "contract.json", "observations.json", "receiver-controls.csv",
    "crossing.json", "phase-gate.json", "audit.json", "manifest.json",
})
IMPLEMENTATION_PATHS = (
    "materials/mat_spec_005.py",
    "scripts/build_mat_spec_005.py",
)

# Captured from CI by rebuilding MAT-SPEC-004 at its merged implementation;
# replace with all six exact output SHA-256s before promotion from draft.
PARENT_V4_SHA256 = {
    "audit.json": "de8986aea4b20f207efd33977206a310d7164345dc50bc88397c57b22728771c",
    "contract.json": "875ab3cc6c96b18a22ebf10593f09604bad2cf1c464622d7bb52b13bc61175eb",
    "manifest.json": "dff08e5ebf6c9acaad2ab83f03b1e04df1bbf883aeae146445be3e6c3e64e637",
    "observations.json": "71fa17c08b3a134b544a2565f3295a9bb9938ed6a7ffc2dbfd77e305381acc90",
    "phase-gate.json": "63f4ee107086c10a9197678a2a99d5e8b99975f0e2107ceaeb37fe69ca84d52e",
    "temperature-controls.csv": (
        "7ce8853422f93a3dd98817cd14a41e66ba5720c5c79fdd58f25154f74c616715"
    ),
}


EXPECTED_META = {
    "source_title": "The Observed Properties of Liquid Helium at the Saturated Vapor Pressure",
    "authors": [
        "Russell J. Donnelly",
        "Carlo F. Barenghi"
    ],
    "citation": "J. Phys. Chem. Ref. Data 27, 1217-1274 (1998)",
    "doi": "10.1063/1.556028",
    "source_pdf": "https://srd.nist.gov/jpcrdreprint/1.556028.pdf",
    "source_website": "https://www.mas.ncl.ac.uk/helium/",
    "publisher_notice": (
        "1998 AIP/ACS, original publication copyright retained; numerical "
        "facts selectively transcribed with attribution"
    ),
    "source_type": (
        "experiment-based evaluated reference tables and spline "
        "recommendations; not original individual-run measurements"
    ),
    "condition": "liquid helium-4 at saturated vapor pressure, ITS-90 temperature",
    "lambda_temperature_K": "2.1768",
    "table_3_3": "recommended first sound speed u1 (m/s), printed page 1230, PDF page index 14",
    "table_4_3": (
        "recommended second sound speed u2 (m/s) in helium II, printed page "
        "1233, PDF page index 17; zero at lambda is a recommended boundary "
        "value"
    ),
    "table_7_4": (
        "recommended heat capacity Cs (J/mol K), printed page 1241, PDF page "
        "index 25; undefined at lambda point"
    ),
    "selected_rows": 14,
    "data_sha256": "e39c29c8dab12a789d6a80d86487c61a4b25c53b68a58d83a88f03bb66755b8e",
    "selection": (
        "predeclared for MAT-SPEC-005 after reference inspection; sparse "
        "exact crossing entries and one distant row each side; not random or "
        "independently held out"
    ),
    "measurement_errors": (
        "per-row experimental error/covariance not given in recommended "
        "Tables 3.3, 4.3, 7.4; encode null"
    ),
    "missingness": (
        "blank means not tabulated at that exact T or outside property "
        "domain; never replace with zero"
    ),
    "phase_labels": (
        "context only from reference lambda point at SVP; not independently "
        "measured row-level phase labels"
    ),
    "data_rights": (
        "small excerpt of factual numerical values; underlying source "
        "publication not re-licensed"
    ),
    "source_independence": (
        "one evaluated compilation assembled from earlier experiments; "
        "separate columns are not source-separated independent trials"
    )
}

EXPECTED_SPEC = {
    "profile": "MAT-SPEC-005",
    "version": "0.1.0",
    "name": "Two-sided helium lambda-point reference and phase-witness gate",
    "parent_profile": "MAT-SPEC-004 v0.1.0",
    "parent_commit": "eac0659cbae1392bf63632ec8138005367e63304",
    "foundational_doi": "10.5281/zenodo.24062652",
    "source_doi": "10.1063/1.556028",
    "data_sha256": "e39c29c8dab12a789d6a80d86487c61a4b25c53b68a58d83a88f03bb66755b8e",
    "sample_count": 14,
    "lambda_K": "2.1768",
    "source_conditions": "helium-4 saturated vapour pressure, ITS-90, compiled reference tables",
    "temperature_regions": (
        "T < lambda context He-II, T == lambda reference boundary, T > lambda "
        "context He-I; NOT independent labels"
    ),
    "property_scales": {
        "first_sound_m_per_s": "2 Hz/(m/s)",
        "second_sound_m_per_s": "40 Hz/(m/s)",
        "heat_capacity_J_per_mol_K": "16 Hz/(J/mol/K)"
    },
    "receiver": (
        "exact rational authored frequency targets plus 12-TET A4=440 "
        "symbolic notes, no MIDI export"
    ),
    "zero_rule": (
        "second_sound at lambda is published zero reference boundary, "
        "unpitched; not an observed above-transition non-detection"
    ),
    "missing_rule": (
        "null above-domain second sound or missing heat capacity remains null "
        "and unpitched; no zero substitution"
    ),
    "uncertainty": "per-row measurement uncertainties absent; never infer from printed precision",
    "crossing_pair_K": [
        "2.1767",
        "2.1769"
    ],
    "claim": (
        "two-sided evaluated reference comparison only; not an independently "
        "phase-labelled classifier, calibrated uncertainty analysis or "
        "held-out study"
    ),
    "audio": "root symbolic JSON/CSV only, no PCM or rendered audio"
}

def _strict_number(value: str) -> Fraction:
    """Only non-negative finite decimal/scientific-notation source strings."""
    if (
        not isinstance(value, str)
        or len(value) > 32
        or re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[Ee][+-]?[0-9]+)?", value)
        is None
    ):
        raise ValueError("invalid reference numeric representation")
    try:
        out = Fraction(value)
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        raise ValueError("invalid reference numeric representation") from exc
    if out < 0:
        raise ValueError("negative reference observable")
    return out


def _context(t: Fraction) -> str:
    if t < LAMBDA:
        return "CONTEXT_HE_II"
    if t > LAMBDA:
        return "CONTEXT_HE_I"
    return "LAMBDA_REFERENCE_BOUNDARY"


def parse_reference(raw: bytes) -> list[dict]:
    if mat_spec.sha256(raw) != DATA_SHA256:
        raise ValueError("NIST evaluated-reference source SHA-256 mismatch")
    try:
        rows = list(csv.reader(io.StringIO(raw.decode("ascii")), strict=True))
    except (UnicodeError, csv.Error) as exc:
        raise ValueError("malformed NIST reference excerpt") from exc
    if (
        len(rows) != len(SELECTED_T) + 1
        or tuple(rows[0]) != COLUMN_NAMES
        or any(len(row) != len(COLUMN_NAMES) for row in rows)
        or tuple(row[0] for row in rows[1:]) != SELECTED_T
    ):
        raise ValueError("unexpected NIST excerpt column/temperature layout")
    result = []
    for t, first, second, heat in rows[1:]:
        temperature = _strict_number(t)
        regime = _context(temperature)
        if temperature <= 0 or not first:
            raise ValueError("invalid reference temperature/first-sound value")
        original = dict(zip(COLUMN_NAMES, (t, first, second or None, heat or None), strict=True))
        for name in SOURCE_PROPERTIES:
            if original[name] is not None:
                _strict_number(original[name])
        if regime == "CONTEXT_HE_II" and not second:
            raise ValueError("missing expected He-II second sound reference")
        if regime == "LAMBDA_REFERENCE_BOUNDARY" and (
            second != "0.000E+0" or heat
        ):
            raise ValueError("lambda boundary zeros/null semantics drift")
        if regime == "CONTEXT_HE_I" and second:
            raise ValueError("normal-fluid second sound must be out of table domain")
        result.append({
            **original,
            "temperature_regime_context": regime,
            "context_is_independent_phase_label": False,
            "data_kind": "evaluated_reference_compilation",
            "first_sound_status": "RECOMMENDED",
            "second_sound_status": (
                "RECOMMENDED"
                if regime == "CONTEXT_HE_II"
                else "LAMBDA_LIMIT_VALUE"
                if regime == "LAMBDA_REFERENCE_BOUNDARY"
                else "OUTSIDE_RECOMMENDED_DOMAIN"
            ),
            "heat_capacity_status": (
                "LAMBDA_UNDEFINED"
                if regime == "LAMBDA_REFERENCE_BOUNDARY"
                else "NOT_TABULATED_AT_SELECTED_T"
                if original["heat_capacity_J_per_mol_K"] is None
                else "RECOMMENDED"
            ),
            "reported_measurement_uncertainty": {
                name: None for name in SOURCE_PROPERTIES
            },
            "independent_row_phase_witness": None,
        })
    return result


def map_receivers(observations: list[dict]) -> list[dict]:
    """Map physical observables separately, preserving null and true zero."""
    results = []
    for item in observations:
        for name, factor in SCALES.items():
            source = item[name]
            numeric = None if source is None else _strict_number(source)
            frequency = None if numeric is None else factor * numeric
            note = None if frequency is None else mat_spec.nearest_midi(frequency)
            results.append({
                "temperature_K": item["temperature_K"],
                "property": name,
                "reported_value": source,
                "reported_uncertainty": None,
                "data_kind": item["data_kind"],
                "measurement_status": (
                    item["first_sound_status"]
                    if name == "first_sound_m_per_s"
                    else item["second_sound_status"]
                    if name == "second_sound_m_per_s"
                    else item["heat_capacity_status"]
                ),
                "regime_context": item["temperature_regime_context"],
                "frequency_target_Hz": (
                    None if frequency is None else str(frequency)
                ),
                "nearest_midi_note": note,
                "cents_error": (
                    None if note is None else mat_spec.cents_error(frequency, note)
                ),
                "zero_unpitched": numeric == 0 if numeric is not None else False,
                "missing_not_zero": numeric is None,
            })
    return results


def crossing_reference(observations: list[dict], mapped: list[dict]) -> dict:
    """Exact near-lambda reference differences, no significance inference."""
    by_t = {r["temperature_K"]: r for r in observations}
    low, high = by_t["2.1767"], by_t["2.1769"]
    midpoint = by_t["2.1768"]
    if (
        low["temperature_regime_context"] != "CONTEXT_HE_II"
        or high["temperature_regime_context"] != "CONTEXT_HE_I"
        or midpoint["temperature_regime_context"] != "LAMBDA_REFERENCE_BOUNDARY"
    ):
        raise ValueError("transition context order drift")
    first_delta = (
        Fraction(high["first_sound_m_per_s"])
        - Fraction(low["first_sound_m_per_s"])
    )
    heat_delta = (
        Fraction(high["heat_capacity_J_per_mol_K"])
        - Fraction(low["heat_capacity_J_per_mol_K"])
    )
    paired = {
        name: [
            next(x for x in mapped if x["temperature_K"] == temp and x["property"] == name)
            for temp in ("2.1767", "2.1769")
        ]
        for name in ("first_sound_m_per_s", "heat_capacity_J_per_mol_K")
    }
    if not all(
        pair[0]["frequency_target_Hz"] is not None
        and pair[1]["frequency_target_Hz"] is not None
        for pair in paired.values()
    ):
        raise ValueError("incomplete crossing comparison")
    return {
        "contextual_lambda_K": "2.1768",
        "pressure_condition": "SVP per evaluated Donnelly-Barenghi reference",
        "nearest_below_K": low["temperature_K"],
        "nearest_above_K": high["temperature_K"],
        "first_sound_difference_above_minus_below_m_per_s": str(first_delta),
        "heat_capacity_difference_above_minus_below_J_per_mol_K": str(heat_delta),
        "second_sound_below_m_per_s": low["second_sound_m_per_s"],
        "second_sound_at_lambda": {
            "value": midpoint["second_sound_m_per_s"],
            "status": "LAMBDA_LIMIT_VALUE_NOT_INDEPENDENT_DETECTION",
        },
        "second_sound_above": None,
        "second_sound_above_status": "NOT_TABULATED_OUTSIDE_DOMAIN_NOT_ZERO",
        "heat_capacity_at_lambda": None,
        "heat_capacity_at_lambda_status": "UNDEFINED_IN_REFERENCE_TABLE",
        "receiver_notes_below_above": {
            name: [item["nearest_midi_note"] for item in pair]
            for name, pair in paired.items()
        },
        "physical_significance_test": "NOT_PERFORMED_NO_REPORTED_PER_ROW_ERRORS",
        "phase_classification_test": "NOT_PERFORMED",
    }


def evidence_gate(observations: list[dict]) -> dict:
    """Cross-boundary tables admitted; independent phase witness still blocked."""
    regimes = [row["temperature_regime_context"] for row in observations]
    if (
        len(observations) != len(SELECTED_T)
        or regimes.count("CONTEXT_HE_II") != 9
        or regimes.count("LAMBDA_REFERENCE_BOUNDARY") != 1
        or regimes.count("CONTEXT_HE_I") != 4
        or tuple(row["temperature_K"] for row in observations) != SELECTED_T
        or any(
            row["temperature_regime_context"] != _context(Fraction(row["temperature_K"]))
            or row.get("data_kind") != "evaluated_reference_compilation"
            or row.get("context_is_independent_phase_label") is not False
            or row.get("independent_row_phase_witness") is not None
            or (
                not isinstance(row.get("reported_measurement_uncertainty"), dict)
                or set(row["reported_measurement_uncertainty"]) != set(SOURCE_PROPERTIES)
                or any(
                    row["reported_measurement_uncertainty"][name] is not None
                    for name in SOURCE_PROPERTIES
                )
            )
            for row in observations
        )
    ):
        raise ValueError("unfrozen or forged phase reference label")
    return {
        "cross_transition_reference": "REPLAY_VERIFIED",
        "independent_phase_witness": "BLOCKED_INSUFFICIENT_INDEPENDENCE_AND_UNCERTAINTY",
        "observations": {
            "context_He_II": 9,
            "lambda_reference": 1,
            "context_He_I": 4,
            "independently_witnessed_He_II": 0,
            "independently_witnessed_He_I": 0,
        },
        "missing_evidence": [
            "RECOMMENDED_TABLES_ARE_NOT_RAW_MEASUREMENTS",
            "NO_INDEPENDENT_ROW_LEVEL_PHASE_LABELS",
            "NO_PER_ROW_EXPERIMENTAL_UNCERTAINTY_OR_COVARIANCE",
            "NO_ABOVE_LAMBDA_SECOND_SOUND_NON_DETECTION_OBSERVATION",
            "NO_SOURCE_SEPARATED_PREREGISTERED_HELD_OUT_EXPERIMENT",
        ],
        "phase_classifier_trained": False,
        "phase_accuracy": None,
        "heldout_phase_accuracy": None,
        "listening_discrimination": "NOT_TESTED",
        "critical_exponent": None,
        "boundary": (
            "A physical transition is established in the reference literature. "
            "This selected table does not independently validate classifier predictions."
        ),
    }


def audit(observations: list[dict], controls: list[dict]) -> dict:
    counts = {}
    exact_checks = 0
    for name, factor in SCALES.items():
        selected = [
            row for row in controls if row["property"] == name
            and row["reported_value"] is not None
        ]
        targets = [Fraction(row["frequency_target_Hz"]) for row in selected]
        source = [Fraction(row["reported_value"]) for row in selected]
        for original, mapped in zip(source, targets, strict=True):
            if mapped / factor != original:
                raise ValueError("common-scale property roundtrip mismatch")
            exact_checks += 1
        notes = [row["nearest_midi_note"] for row in selected]
        counts[name] = {
            "tabulated": len(selected),
            "missing": len(observations) - len(selected),
            "unique_reported_values": len(set(source)),
            "unique_frequency_targets": len(set(targets)),
            "unique_symbolic_midi_notes": len({n for n in notes if n is not None}),
            "unpitched_true_zero": sum(n is None for n in notes),
            "unique_controls_including_unpitched": len(set(notes)),
            "colliding_row_pairs_after_midi": sum(
                a == b for a, b in combinations(notes, 2)
            ),
        }
    u2 = [r for r in controls if r["property"] == "second_sound_m_per_s"]
    if (
        sum(r["missing_not_zero"] for r in u2) != 4
        or sum(r["zero_unpitched"] for r in u2) != 1
        or any(
            r["nearest_midi_note"] is not None
            for r in u2 if r["missing_not_zero"] or r["zero_unpitched"]
        )
    ):
        raise ValueError("zero/absent second sound distinction failed")
    return {
        "profile": PROFILE,
        "version": VERSION,
        "source_row_count": len(observations),
        "source_property_counts": counts,
        "exact_fraction_target_roundtrip_checks": exact_checks,
        "unpitched_lambda_reference_second_sound": 1,
        "out_of_domain_second_sound_not_zero": 4,
        "temperature_order_and_source_identity": "PINNED",
        "error_intervals": "NOT_COMPUTED_ERRORS_UNAVAILABLE",
        "runtime_audio_generated": False,
        "receiver_interpretation": (
            "separate authored scales; Hz targets do not equal unscaled physical "
            "acoustic frequencies and cannot establish physical phase"
        ),
    }


def _csv(mapped: list[dict]) -> bytes:
    columns = tuple(mapped[0])
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(mapped)
    return handle.getvalue().encode("ascii")


def build_evidence(root: Path) -> dict[str, bytes]:
    parent = mat_spec_004.build_evidence(root)
    if set(parent) != mat_spec_004.OUTPUT_NAMES:
        raise ValueError("unexpected MAT-SPEC-004 parent file membership")
    parent_hashes = {name: mat_spec.sha256(raw) for name, raw in parent.items()}
    if parent_hashes != PARENT_V4_SHA256:
        raise ValueError("frozen MAT-SPEC-004 parent SHA-256 mismatch")
    manifest = json.loads(parent["manifest.json"])
    if (
        manifest.get("profile") != "MAT-SPEC-004"
        or manifest.get("version") != "0.1.0"
        or manifest.get("parent_commit") != mat_spec_004.PARENT_COMMIT
        or manifest.get("source", {}).get("doi") != mat_spec_004.SOURCE_DOI
    ):
        raise ValueError("frozen MAT-SPEC-004 parent manifest identity mismatch")
    for name, digest in manifest["outputs"].items():
        if name not in parent or mat_spec.sha256(parent[name]) != digest["sha256"]:
            raise ValueError("MAT-SPEC-004 parent receipt inconsistency")

    raw_data = mat_spec.read_regular(root / DATA_PATH)
    raw_spec = mat_spec.read_regular(root / SPEC_PATH)
    raw_meta = mat_spec.read_regular(root / META_PATH)
    # This contract deliberately contains only static, reviewable keys.
    spec = json.loads(raw_spec)
    meta = json.loads(raw_meta)
    if spec != EXPECTED_SPEC or meta != EXPECTED_META:
        raise ValueError("MAT-SPEC-005 specification or source metadata drift")
    observations = parse_reference(raw_data)
    mapped = map_receivers(observations)
    report = audit(observations, mapped)
    crossing = crossing_reference(observations, mapped)
    gate = evidence_gate(observations)

    artifacts = {
        "contract.json": mat_spec.canonical_json(spec),
        "observations.json": mat_spec.canonical_json({
            "provenance": meta, "observations": observations,
        }),
        "receiver-controls.csv": _csv(mapped),
        "crossing.json": mat_spec.canonical_json(crossing),
        "phase-gate.json": mat_spec.canonical_json(gate),
        "audit.json": mat_spec.canonical_json(report),
    }
    implementation = {
        path: mat_spec.sha256(mat_spec.read_regular(root / path))
        for path in IMPLEMENTATION_PATHS
    }
    receipt = {
        "profile": PROFILE, "version": VERSION,
        "parent_commit": PARENT_COMMIT,
        "parent_v4_artifacts": {
            name: {"sha256": digest, "bytes": len(parent[name])}
            for name, digest in sorted(parent_hashes.items())
        },
        "original_mat_spec_001_doi": FOUNDATIONAL_DOI,
        "source": {
            "doi": SOURCE_DOI, "pdf": meta["source_pdf"],
            "kind": "attributed evaluated reference excerpt, not raw measurements",
            "path": DATA_PATH,
            "sha256": mat_spec.sha256(raw_data), "bytes": len(raw_data),
        },
        "metadata": {
            "path": META_PATH, "sha256": mat_spec.sha256(raw_meta),
        },
        "contract_input": {
            "path": SPEC_PATH, "sha256": mat_spec.sha256(raw_spec),
        },
        "implementation": implementation,
        "outputs": {
            name: {"sha256": mat_spec.sha256(raw), "bytes": len(raw)}
            for name, raw in sorted(artifacts.items())
        },
        "manifest_self_hash": None,
        "canonical_pcm_sha256": None,
        "canonical_wav_sha256": None,
        "audio_status": "intentionally disabled",
    }
    artifacts["manifest.json"] = mat_spec.canonical_json(receipt)
    return artifacts


def write_evidence(root: Path, destination: str, artifacts: dict[str, bytes]) -> Path:
    """Exclusive no-follow export of declared symbolic files, never sampled audio."""
    path = PurePosixPath(destination)
    if (
        not destination or path.is_absolute() or "\\" in destination
        or any(piece in {"", ".", ".."} for piece in destination.split("/"))
    ):
        raise ValueError("destination must be a fresh relative directory")
    if set(artifacts) != OUTPUT_NAMES or any(
        PurePosixPath(name).name != name
        or Path(name).suffix not in {".json", ".csv"} for name in artifacts
    ):
        raise ValueError("forbidden artifact type or membership")
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
        output_fd = fds[-1]
        for name in sorted(artifacts):
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode=0o644, dir_fd=output_fd,
            )
            with os.fdopen(fd, "wb") as handle:
                handle.write(artifacts[name])
        actual = os.fstat(output_fd)
        visible = os.stat(path.parts[-1], dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISDIR(visible.st_mode) or (
            actual.st_dev, actual.st_ino
        ) != (visible.st_dev, visible.st_ino):
            raise ValueError("destination changed during export")
    finally:
        for fd in reversed(fds):
            os.close(fd)
    return root / path
