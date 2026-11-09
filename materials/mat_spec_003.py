"""MAT-SPEC-003: bounded dispersion-mode descriptors and receiver discrimination.

SPDX-License-Identifier: MPL-2.0
Copyright (c) 2026 Trent Slade / QSOL-IMC.

All values are symbolic. The program neither generates PCM nor infers a phase.
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

from materials import mat_spec, mat_spec_002

PROFILE = "MAT-SPEC-003"
VERSION = "0.1.0"
SOURCE_SHA256 = mat_spec.SOURCE_SHA256
RELATED_DOI = "10.5281/zenodo.24062652"
PARENT_002_COMMIT = "c400a27e16cc1ed63efc6657dbdd25d003b7bdbb"
SPEC_PATH = "spec/mat-spec-003.v0.1.json"
IMPLEMENTATION_PATHS = (
    "materials/mat_spec_003.py",
    "scripts/build_mat_spec_003.py",
)
OUTPUT_NAMES = frozenset({
    "contract.json",
    "features.csv",
    "feature-intervals.json",
    "pressure-discrimination.csv",
    "controls.json",
    "manifest.json",
})
PRIMARY_WINDOWS = {
    "phonon": ("0.150", "0.450"),
    "maxon": ("0.750", "1.400"),
    "roton": ("1.600", "2.150"),
}
ALTERNATE_WINDOWS = {
    "phonon": ("0.150", "0.300"),
    "maxon": ("0.900", "1.250"),
    "roton": ("1.800", "2.050"),
}
MODES = ("phonon", "maxon", "roton")
PARENT_V2_SHA256 = None  # Replace with all five captured CI baseline digests.
EXPECTED_SPEC = {
    "profile": PROFILE,
    "version": VERSION,
    "source_sha256": SOURCE_SHA256,
    "related_doi": RELATED_DOI,
    "parent_commit": PARENT_002_COMMIT,
    "primary_windows_inverse_angstrom": {
        k: list(v) for k, v in PRIMARY_WINDOWS.items()
    },
    "alternate_windows_inverse_angstrom": {
        k: list(v) for k, v in ALTERNATE_WINDOWS.items()
    },
    "phonon": "origin-constrained unweighted slope in meV*angstrom",
    "extrema": "windowed maxon maximum and roton minimum; no curve fit",
    "bounds": "independent adversarial boxes from reported +/-errE; no distribution",
    "missing": "mark partial; do not compare windows with any missing observations",
    "receiver": "compare exact nominal maxon/roton energies, two-value ranks and 12-TET",
    "zero_and_audio": "no PCM/WAV; zero not silently pitched",
    "claim": "windowed descriptors, not phase, sound-speed, E8 or perceptual identification",
}


def _observation_values(row: dict) -> tuple[Fraction, Fraction]:
    energy = Fraction(row["energy_meV"])
    error = Fraction(row["reported_energy_error_meV"])
    if energy < 0 or error < 0:
        raise ValueError("negative energy/error")
    return energy, error


def _bounds(row: dict) -> tuple[Fraction, Fraction]:
    energy, error = _observation_values(row)
    return energy - error, energy + error


def scale_observation(row: dict, factor: Fraction) -> dict:
    """Explicit positive metamorphic rescaling, including reported error."""
    if factor <= 0:
        raise ValueError("factor must be positive")
    if row["status"] == "missing":
        return dict(row)
    if row["status"] != "tabulated":
        raise ValueError("invalid observation status")
    energy, error = _observation_values(row)
    return {
        **row,
        "energy_meV": str(energy * factor),
        "reported_energy_error_meV": str(error * factor),
    }


def mode_feature(
    series: list[dict], mode: str, window: tuple[str, str]
) -> dict:
    """Nominal extrema and worst-case intervals from reported finite-grid data.

    A missing point makes the complete-window descriptor ineligible for
    cross-pressure discrimination. Candidate q values are possible among
    *observed* rows only, not an interpolation or a continuous fitted mode.
    """
    if mode not in MODES:
        raise ValueError("unknown physical-mode descriptor")
    lo, hi = (Fraction(x) for x in window)
    if not 0 < lo < hi:
        raise ValueError("invalid wavevector window")
    selected = [
        r for r in series if lo <= Fraction(r["q_inverse_angstrom"]) <= hi
    ]
    q_values = [Fraction(r["q_inverse_angstrom"]) for r in selected]
    if not selected or any(a >= b for a, b in zip(q_values, q_values[1:])):
        raise ValueError("empty, unordered or duplicate wavevector window")
    if any(r["status"] not in {"tabulated", "missing"} for r in selected):
        raise ValueError("invalid observation status")
    valid = [r for r in selected if r["status"] == "tabulated"]
    missing = len(selected) - len(valid)
    status = "MISSING" if not valid else "PARTIAL" if missing else "COMPLETE"
    result = {
        "mode": mode,
        "window_q_inverse_angstrom": list(window),
        "window_total": len(selected),
        "valid": len(valid),
        "missing": missing,
        "status": status,
        "nominal": None,
        "lower": None,
        "upper": None,
        "unit": "meV*angstrom" if mode == "phonon" else "meV",
        "nominal_q_inverse_angstrom": None,
        "nominal_q_interior": None,
        "candidate_q_inverse_angstrom": [],
        "unique_extremum_certified": False,
        "quantized_midi_note": None,
    }
    if not valid:
        return result

    if mode == "phonon":
        q = [Fraction(r["q_inverse_angstrom"]) for r in valid]
        entries = [_observation_values(r) for r in valid]
        denominator = sum((v * v for v in q), Fraction())
        if denominator == 0:
            raise ValueError("zero wavevector slope denominator")
        slope = sum((v * e for v, (e, _) in zip(q, entries, strict=True)), Fraction())
        spread = sum((v * d for v, (_, d) in zip(q, entries, strict=True)), Fraction())
        result.update(
            nominal=str(slope / denominator),
            lower=str((slope - spread) / denominator),
            upper=str((slope + spread) / denominator),
        )
        return result

    is_max = mode == "maxon"
    rank_key = (lambda row: _observation_values(row)[0])
    if is_max:
        selected_row = min(valid, key=lambda r: (-rank_key(r), Fraction(r["q_inverse_angstrom"])))
        lower = max(_bounds(row)[0] for row in valid)
        upper = max(_bounds(row)[1] for row in valid)
        candidates = [
            r for r in valid if _bounds(r)[1] >= lower
        ]
    else:
        selected_row = min(valid, key=lambda r: (rank_key(r), Fraction(r["q_inverse_angstrom"])))
        lower = min(_bounds(row)[0] for row in valid)
        upper = min(_bounds(row)[1] for row in valid)
        candidates = [
            r for r in valid if _bounds(r)[0] <= upper
        ]
    if lower > upper:
        raise ValueError("invalid extremum interval")
    nominal_energy, _ = _observation_values(selected_row)
    q_nominal = Fraction(selected_row["q_inverse_angstrom"])
    candidate_q = [r["q_inverse_angstrom"] for r in candidates]
    if is_max:
        robust = all(
            _bounds(selected_row)[0] > _bounds(other)[1]
            for other in valid if other is not selected_row
        )
    else:
        robust = all(
            _bounds(selected_row)[1] < _bounds(other)[0]
            for other in valid if other is not selected_row
        )
    result.update(
        nominal=str(nominal_energy),
        lower=str(lower),
        upper=str(upper),
        nominal_q_inverse_angstrom=selected_row["q_inverse_angstrom"],
        nominal_q_interior=(lo < q_nominal < hi),
        candidate_q_inverse_angstrom=candidate_q,
        unique_extremum_certified=(not missing and robust),
        quantized_midi_note=mat_spec.nearest_midi(400 * nominal_energy),
    )
    return result


def interval_decision(a: dict, b: dict) -> str:
    """Only fully populated windows are eligible for interval decisions."""
    if a["status"] != "COMPLETE" or b["status"] != "COMPLETE":
        return "INELIGIBLE"
    if Fraction(a["upper"]) < Fraction(b["lower"]):
        return "a_below_b"
    if Fraction(b["upper"]) < Fraction(a["lower"]):
        return "b_below_a"
    return "overlap"


def window_features(
    by_pressure: dict[str, list[dict]], windows: dict[str, tuple[str, str]]
) -> dict[str, dict[str, dict]]:
    result = {}
    for pressure in mat_spec.PRESSURES:
        result[pressure] = {
            mode: mode_feature(by_pressure[pressure], mode, windows[mode])
            for mode in MODES
        }
    return result


def receiver_controls(features: dict[str, dict[str, dict]]) -> dict:
    """Compare only physically commensurate *energies*, not the phonon slope."""
    profiles = {}
    for pressure in mat_spec.PRESSURES:
        pair = [features[pressure][name] for name in ("maxon", "roton")]
        if any(x["status"] != "COMPLETE" for x in pair):
            continue
        values = tuple(Fraction(p["nominal"]) for p in pair)
        profiles[pressure] = {
            "nominal_energy_meV": [str(v) for v in values],
            "q_inverse_angstrom": [p["nominal_q_inverse_angstrom"] for p in pair],
            "exact_400_Hz_per_meV": [str(400 * v) for v in values],
            "rank_offsets": mat_spec.rank_offsets(list(values)),
            "quantized_midi_notes": [mat_spec.nearest_midi(400 * v) for v in values],
        }
    fields = {
        "exact_common_scale": "exact_400_Hz_per_meV",
        "rank": "rank_offsets",
        "quantized_midi": "quantized_midi_notes",
    }
    counts = {}
    for name, key in fields.items():
        signatures = [tuple(p[key]) for p in profiles.values()]
        counts[name] = {
            "complete_profiles": len(signatures),
            "unique_contours": len(set(signatures)),
            "colliding_pairs": sum(
                a == b for a, b in combinations(signatures, 2)
            ),
        }
    return {
        "profiles": profiles,
        "collision_audit": counts,
        "q_coordinates_in_symbolic_receiver": False,
        "discrimination_scope": "nominal pairwise receiver identity; no listener test",
    }


def within_pressure_mode_gap(features: dict[str, dict[str, dict]]) -> dict:
    """Maxon/roton gap and ratio: meaningful only with both complete windows."""
    result = {}
    for pressure in mat_spec.PRESSURES:
        peak, trough = (features[pressure][m] for m in ("maxon", "roton"))
        if peak["status"] != "COMPLETE" or trough["status"] != "COMPLETE":
            result[pressure] = {"status": "INELIGIBLE", "reason": "missing window observations"}
            continue
        pl, pu = Fraction(peak["lower"]), Fraction(peak["upper"])
        rl, ru = Fraction(trough["lower"]), Fraction(trough["upper"])
        gap = {
            "lower_meV": str(pl - ru),
            "upper_meV": str(pu - rl),
            "reported_boxes_disjoint": pl > ru or rl > pu,
        }
        if rl <= 0:
            ratio = {"status": "UNBOUNDED_BY_POSITIVE_DENOMINATOR"}
        else:
            ratio = {
                "status": "BOUNDED",
                "nominal": str(Fraction(peak["nominal"]) / Fraction(trough["nominal"])),
                "lower": str(pl / ru),
                "upper": str(pu / rl),
            }
        result[pressure] = {"status": "COMPLETE", "gap": gap, "ratio": ratio}
    return result


def _feature_csv(features: dict[str, dict[str, dict]]) -> bytes:
    columns = (
        "pressure_bar", "mode", "status", "window_total", "valid", "missing",
        "unit", "nominal", "lower", "upper", "nominal_q_inverse_angstrom",
        "nominal_q_interior", "candidate_q_count", "unique_extremum_certified",
        "quantized_midi_note",
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for pressure in mat_spec.PRESSURES:
        for mode in MODES:
            item = features[pressure][mode]
            writer.writerow({
                "pressure_bar": pressure,
                **{key: item[key] for key in columns if key not in (
                    "pressure_bar", "candidate_q_count"
                )},
                "candidate_q_count": len(item["candidate_q_inverse_angstrom"]),
            })
    return stream.getvalue().encode("ascii")


def _pressure_csv(features: dict[str, dict[str, dict]]) -> tuple[bytes, dict]:
    columns = ("mode", "pressure_a_bar", "pressure_b_bar", "comparison")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    counts = {
        mode: dict.fromkeys(("a_below_b", "b_below_a", "overlap", "INELIGIBLE"), 0)
        for mode in MODES
    }
    for mode in MODES:
        for a, b in combinations(mat_spec.PRESSURES, 2):
            comparison = interval_decision(features[a][mode], features[b][mode])
            counts[mode][comparison] += 1
            writer.writerow({
                "mode": mode,
                "pressure_a_bar": a,
                "pressure_b_bar": b,
                "comparison": comparison,
            })
    if any(sum(k.values()) != 21 for k in counts.values()):
        raise ValueError("pressure-pair feature conservation failed")
    return stream.getvalue().encode("ascii"), counts


def _assert_scale_metamorphism(
    by_pressure: dict[str, list[dict]], features: dict[str, dict[str, dict]]
) -> int:
    count = 0
    for pressure in mat_spec.PRESSURES:
        doubled = [scale_observation(r, Fraction(2)) for r in by_pressure[pressure]]
        for mode in MODES:
            old = features[pressure][mode]
            new = mode_feature(doubled, mode, PRIMARY_WINDOWS[mode])
            for name in ("nominal", "lower", "upper"):
                expected = None if old[name] is None else str(2 * Fraction(old[name]))
                if new[name] != expected:
                    raise ValueError("positive rescaling of mode descriptor failed")
            if any(new[key] != old[key] for key in (
                "status", "missing", "valid", "nominal_q_inverse_angstrom",
                "candidate_q_inverse_angstrom", "unique_extremum_certified",
            )):
                raise ValueError("positive rescaling changed spatial mode selection")
            count += 1
    return count


def build_evidence(root: Path) -> dict[str, bytes]:
    """Run fully verified MAT-SPEC-002 and seal a separate physical-mode view."""
    parent = mat_spec_002.build_evidence(root)
    parent_digests = {name: mat_spec.sha256(data) for name, data in parent.items()}
    if PARENT_V2_SHA256 is not None and parent_digests != PARENT_V2_SHA256:
        raise ValueError("archived MAT-SPEC-002 baseline output SHA-256 mismatch")
    parent_manifest = json.loads(parent["manifest.json"])
    if (
        parent_manifest.get("profile") != "MAT-SPEC-002"
        or parent_manifest.get("version") != "0.1.0"
        or parent_manifest.get("source_sha256") != SOURCE_SHA256
        or parent_manifest.get("parent_doi") != RELATED_DOI
    ):
        raise ValueError("unexpected MAT-SPEC-002 parent identity")
    for name, receipt in parent_manifest["outputs"].items():
        if mat_spec.sha256(parent[name]) != receipt["sha256"]:
            raise ValueError("MAT-SPEC-002 parent receipt inconsistency")
    raw_spec = mat_spec.read_regular(root / SPEC_PATH)
    try:
        spec = json.loads(raw_spec)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("invalid mode contract") from exc
    if spec != EXPECTED_SPEC:
        raise ValueError("MAT-SPEC-003 frozen mode contract mismatch")
    original = mat_spec.build_bundle(root)
    if {
        name: mat_spec.sha256(data) for name, data in original.items()
    } != mat_spec_002.PARENT_ARTIFACT_SHA256:
        raise ValueError("MAT-SPEC-001 preserved ancestor drift")
    observations = json.loads(original["observations.json"])["observations"]
    by_pressure = mat_spec_002.index_observations(observations)
    features = window_features(by_pressure, PRIMARY_WINDOWS)
    alternatives = window_features(by_pressure, ALTERNATE_WINDOWS)
    pressure_bytes, pair_counts = _pressure_csv(features)
    controls = {
        "profile": PROFILE,
        "version": VERSION,
        "mode_gap_and_ratio_by_pressure": within_pressure_mode_gap(features),
        "receiver": receiver_controls(features),
        "alternate_windows": alternatives,
        "pressure_pair_interval_counts": pair_counts,
        "metamorphic_checks": {
            "factor_two_energy_and_error": _assert_scale_metamorphism(
                by_pressure, features
            ),
        },
        "observed_input_counts": {
            "tabulated": 7118,
            "missing": 232,
            "q_positions": 1050,
            "pressures": 7,
        },
        "assurance": {
            "replay": "CHECKED_BY_CI",
            "physical_input": "published low-temperature helium measurements",
            "fit_to_dynamic_structure_factor": "NOT_TESTED",
            "normal_superfluid_phase_classification": "NOT_TESTED",
            "absolute_zero_extrapolation": "NOT_TESTED",
            "blind_listener_discrimination": "NOT_TESTED",
            "cobalt_niobate_E8_test": "NOT_TESTED",
            "theory_of_everything": "NOT_CLAIMED",
        },
        "no_sampled_audio_generated": True,
    }
    products = {
        "contract.json": mat_spec.canonical_json(spec),
        "features.csv": _feature_csv(features),
        "feature-intervals.json": mat_spec.canonical_json(features),
        "pressure-discrimination.csv": pressure_bytes,
        "controls.json": mat_spec.canonical_json(controls),
    }
    impl = {
        path: mat_spec.sha256(mat_spec.read_regular(root / path))
        for path in IMPLEMENTATION_PATHS
    }
    manifest = {
        "profile": PROFILE,
        "version": VERSION,
        "related_doi": RELATED_DOI,
        "parent_commit": PARENT_002_COMMIT,
        "parent_v2_artifacts": {
            name: {"sha256": digest, "bytes": len(parent[name])}
            for name, digest in sorted(parent_digests.items())
        },
        "frozen_v1_artifacts": mat_spec_002.PARENT_ARTIFACT_SHA256,
        "source_sha256": SOURCE_SHA256,
        "contract_source": {
            "path": SPEC_PATH,
            "sha256": mat_spec.sha256(raw_spec),
        },
        "implementation": impl,
        "outputs": {
            name: {"sha256": mat_spec.sha256(data), "bytes": len(data)}
            for name, data in sorted(products.items())
        },
        "serialization": "sorted ASCII compact JSON + LF; CSV + LF",
        "manifest_self_hash": None,
        "canonical_pcm_sha256": None,
        "canonical_wav_sha256": None,
        "audio_generated": False,
    }
    products["manifest.json"] = mat_spec.canonical_json(manifest)
    return products


def write_evidence(root: Path, destination: str, artifacts: dict[str, bytes]) -> Path:
    """No-follow, no-overwrite POSIX symbolic output like MAT-SPEC-002."""
    path = PurePosixPath(destination)
    if (
        not destination or path.is_absolute() or "\\" in destination
        or any(part in {"", ".", ".."} for part in destination.split("/"))
    ):
        raise ValueError("destination must be a new relative directory")
    if set(artifacts) != OUTPUT_NAMES or any(
        name != PurePosixPath(name).name
        or Path(name).suffix not in {".csv", ".json"} for name in artifacts
    ):
        raise ValueError("only declared symbolic outputs allowed")
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
        out_fd = fds[-1]
        for name in sorted(artifacts):
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode=0o644, dir_fd=out_fd,
            )
            with os.fdopen(fd, "wb") as stream:
                stream.write(artifacts[name])
        opened = os.fstat(out_fd)
        visible = os.stat(path.parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISDIR(visible.st_mode) or (
            opened.st_dev, opened.st_ino
        ) != (visible.st_dev, visible.st_ino):
            raise ValueError("output directory changed during export")
    finally:
        for fd in reversed(fds):
            os.close(fd)
    return root / path
