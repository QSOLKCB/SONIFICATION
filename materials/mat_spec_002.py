"""MAT-SPEC-002: exact interval and sampling sensitivity audit of MAT-SPEC-001.

SPDX-License-Identifier: MPL-2.0
Copyright (c) 2026 Trent Slade / QSOL-IMC.

Observational numerical evidence only. This module produces no sampled audio.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
from contextlib import suppress
from fractions import Fraction
from itertools import combinations
from pathlib import Path, PurePosixPath

from materials.mat_spec import (
    PRESSURES, SAMPLE_Q, SOURCE_PATH, SOURCE_SHA256,
    build_bundle as build_v1, canonical_json, rank_offsets, sha256,
)

PROFILE = "MAT-SPEC-002"
VERSION = "0.1.0"
PARENT_COMMIT = "195b325097cd01f16e9ca909edd95482d4863c27"
PARENT_DOI = "10.5281/zenodo.24062652"
GRID_SIZE = 1050
TILE_SIZE = 128
SAMPLE_COUNTS = (6, 12, 24, 48)
IMPLEMENTATION_PATHS = ("materials/mat_spec_002.py", "scripts/build_mat_spec_002.py")
OUTPUT_NAMES = frozenset({
    "contract.json", "pressure-pairs.csv", "sampling.json", "audit.json", "manifest.json"
})
RELATIONS = ("a_below_b", "b_below_a", "overlap", "missing")
REVERSE = {
    "a_below_b": "b_below_a", "b_below_a": "a_below_b",
    "overlap": "overlap", "missing": "missing",
}


def interval_relation(a: dict, b: dict) -> str:
    """Compare closed [E-err,E+err] intervals; no confidence interpretation."""
    if a["status"] not in {"missing", "tabulated"} or b["status"] not in {"missing", "tabulated"}:
        raise ValueError("invalid observation status")
    if a["status"] == "missing" or b["status"] == "missing":
        return "missing"
    ea, da = Fraction(a["energy_meV"]), Fraction(a["reported_energy_error_meV"])
    eb, db = Fraction(b["energy_meV"]), Fraction(b["reported_energy_error_meV"])
    if min(ea, da, eb, db) < 0:
        raise ValueError("negative observed energy/error")
    if ea + da < eb - db:
        return "a_below_b"
    if eb + db < ea - da:
        return "b_below_a"
    return "overlap"


def uniform_indices(logical_count: int, sample_count: int) -> tuple[int, ...]:
    """GLUBALL uniform-floor index map; exact integers and no logical allocation."""
    if (
        type(logical_count) is not int or type(sample_count) is not int
        or not (1 <= sample_count <= logical_count <= 1_000_000)
    ):
        raise ValueError("invalid uniform-floor bounds")
    result = tuple(i * logical_count // sample_count for i in range(sample_count))
    if len(set(result)) != sample_count or result[0] != 0 or result[-1] >= logical_count:
        raise ValueError("uniform-floor index invariant failed")
    return result


def index_observations(observations: list[dict]) -> dict[str, list[dict]]:
    """Check a complete aligned q grid; missing measurements remain in place."""
    if len(observations) != GRID_SIZE * len(PRESSURES):
        raise ValueError("unexpected number of observations")
    by_pressure = {p: [] for p in PRESSURES}
    for row in observations:
        pressure = row["pressure_bar"]
        if pressure not in by_pressure:
            raise ValueError("unknown pressure")
        by_pressure[pressure].append(row)
    reference = tuple(row["q_inverse_angstrom"] for row in by_pressure[PRESSURES[0]])
    if len(reference) != GRID_SIZE or len(set(reference)) != GRID_SIZE:
        raise ValueError("invalid q grid")
    for pressure in PRESSURES:
        series = by_pressure[pressure]
        if len(series) != GRID_SIZE or tuple(r["q_inverse_angstrom"] for r in series) != reference:
            raise ValueError("pressure grids are not aligned")
    return by_pressure


def scaled_twice(row: dict) -> dict:
    if row["status"] != "tabulated":
        return row
    return {
        "status": "tabulated",
        "energy_meV": str(2 * Fraction(row["energy_meV"])),
        "reported_energy_error_meV": str(2 * Fraction(row["reported_energy_error_meV"])),
    }


def audit_pairs(by_pressure: dict[str, list[dict]], tile_size: int = TILE_SIZE) -> tuple[list[dict], dict]:
    """Stream 21 matched-q pressure comparisons without materializing pair states.

    Tiling must not change counts, direction, missingness or canonical receipt.
    """
    if type(tile_size) is not int or not 1 <= tile_size <= GRID_SIZE:
        raise ValueError("invalid tile size")
    rows = []
    total = dict.fromkeys(RELATIONS, 0)
    checked = 0
    for pressure_a, pressure_b in combinations(PRESSURES, 2):
        left, right = by_pressure[pressure_a], by_pressure[pressure_b]
        counts = dict.fromkeys(RELATIONS, 0)
        witness = hashlib.sha256(b"MAT-SPEC-002/PAIR-STATUS/v1\x00")
        witness.update(f"{pressure_a}|{pressure_b}\n".encode("ascii"))
        for start in range(0, GRID_SIZE, tile_size):
            for i in range(start, min(GRID_SIZE, start + tile_size)):
                a, b = left[i], right[i]
                state = interval_relation(a, b)
                if state != "missing":
                    if interval_relation(scaled_twice(a), scaled_twice(b)) != state:
                        raise ValueError("positive scale invariance failed")
                    if REVERSE[interval_relation(b, a)] != state:
                        raise ValueError("pair reversal covariance failed")
                    checked += 1
                counts[state] += 1
                witness.update(f"{i}|{a['q_inverse_angstrom']}|{state}\n".encode("ascii"))
        if sum(counts.values()) != GRID_SIZE:
            raise ValueError("pair coverage invariant failed")
        for state in RELATIONS:
            total[state] += counts[state]
        rows.append({
            "pressure_a_bar": pressure_a,
            "pressure_b_bar": pressure_b,
            **counts,
            "comparable": GRID_SIZE - counts["missing"],
            "status_stream_sha256": witness.hexdigest(),
        })
    if sum(total.values()) != GRID_SIZE * 21 or checked != GRID_SIZE * 21 - total["missing"]:
        raise ValueError("full-grid conservation failed")
    return rows, {
        **total, "comparable": checked, "total_q_pressure_pairs": GRID_SIZE * 21,
        "positive_scale_and_reversal_checks": checked,
        "pair_receipt_sha256": sha256(canonical_json(rows)),
        "tile_size": tile_size,
    }


def audit_sampling(by_pressure: dict[str, list[dict]]) -> list[dict]:
    """Alternate q selections are audit controls, not replacements for v1 samples."""
    result = []
    for count in SAMPLE_COUNTS:
        indices = uniform_indices(GRID_SIZE, count)
        complete: dict[str, tuple[tuple, tuple, tuple]] = {}
        incomplete = []
        missing_cells = 0
        for pressure in PRESSURES:
            chosen = [by_pressure[pressure][i] for i in indices]
            missing_cells += sum(p["status"] == "missing" for p in chosen)
            if any(p["status"] == "missing" for p in chosen):
                incomplete.append(pressure)
                continue
            energies = tuple(Fraction(p["energy_meV"]) for p in chosen)
            exact = tuple(Fraction(p["frequency_Hz"]) for p in chosen)
            rank = tuple(rank_offsets(list(energies)))
            midi = tuple(p["midi_note"] for p in chosen)
            complete[pressure] = (exact, rank, midi)
        collisions = {"common_scale": 0, "rank": 0, "quantized_midi": 0}
        for a, b in combinations(complete, 2):
            for label, j in (("common_scale", 0), ("rank", 1), ("quantized_midi", 2)):
                collisions[label] += complete[a][j] == complete[b][j]
        result.append({
            "sampling": "GLUBALL uniform-floor logical(i)=floor(i*1050/R)",
            "sample_count": count, "indices": list(indices),
            "q_inverse_angstrom": [
                by_pressure[PRESSURES[0]][i]["q_inverse_angstrom"] for i in indices
            ],
            "metadata_lane_mod_3": [i % 3 for i in range(count)],
            "complete_pressures_bar": list(complete),
            "incomplete_pressures_bar": incomplete,
            "missing_selected_cells": missing_cells,
            "comparable_pressure_pairs": len(complete) * (len(complete) - 1) // 2,
            "exact_profile_collisions": collisions,
            "scope": "nominal selected-data collisions only; no significance or perceptual inference",
        })
    return result


def build_evidence(root: Path) -> dict[str, bytes]:
    """Derive a separate successor receipt from an independently replayed v1 bundle."""
    original = build_v1(root)
    v1_manifest = json.loads(original["manifest.json"])
    if (
        v1_manifest.get("profile") != "MAT-SPEC-001"
        or v1_manifest.get("version") != "1.0.0"
        or v1_manifest.get("inputs", {}).get(SOURCE_PATH, {}).get("sha256") != SOURCE_SHA256
    ):
        raise ValueError("frozen MAT-SPEC-001 identity mismatch")
    for name, entry in v1_manifest["outputs"].items():
        if name not in original or sha256(original[name]) != entry["sha256"]:
            raise ValueError("parent output receipt mismatch")
    observations = json.loads(original["observations.json"])["observations"]
    by_pressure = index_observations(observations)
    pair_rows, totals = audit_pairs(by_pressure)
    sampled = audit_sampling(by_pressure)
    contract = {
        "profile": PROFILE, "version": VERSION,
        "parent_profile": "MAT-SPEC-001 v1.0.0", "parent_commit": PARENT_COMMIT,
        "related_doi": PARENT_DOI, "source_sha256": SOURCE_SHA256,
        "interval_rule": "closed [E-errE,E+errE] on reported decimals; touching counts as overlap",
        "pair_rule": "all 21 pressure pairs at identical q; retain missing; no interpolation",
        "tiling": "128-observation blocks; identical results required at any valid block size",
        "sampling": "GLUBALL uniform-floor on 1050 ordered q points at R=6,12,24,48",
        "sample_metadata_lane": "i mod 3, not topology or physics",
        "receiver_invariant": "positive common scaling preserves exact interval ordering",
        "source_reuse": "MAT-SPEC-001 verified in-memory observations only",
        "claims": "numerical interval separation and sensitivity only; no uncertainty distribution",
        "physical_phase_inference": "NOT_TESTED",
        "listener_discrimination": "NOT_TESTED",
        "E8_in_helium": "NOT_CLAIMED",
        "audio": "DISABLED",
    }
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=list(pair_rows[0]), lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(pair_rows)
    audit = {
        "profile": PROFILE, "version": VERSION, "full_grid": totals,
        "method": "streaming conservative interval separation, no covariance model",
        "metamorphic": {
            "scale_by_two": "PASS on all comparable matched-q pairs",
            "pressure_order_swap": "PASS on all comparable matched-q pairs",
            "tile_independence": "tested by separate parity regression",
        },
        "interpretation": {
            "separated": "disjoint reported ±errE intervals, not a significance test",
            "overlap": "overlapping or touching reported intervals, not proof of equal spectra",
            "missing": "not comparable; not zero",
            "sampling": "sensitivity control, not unbiased random sampling",
        },
        "assurance": {
            "replay_verification": "software receipts only",
            "empirical_source": "published, processed helium superfluid-regime measurements",
            "phase_classification": "NOT_TESTED",
            "blinded_listening": "NOT_TESTED",
            "independent_physical_replication": "NOT_TESTED",
            "E8_or_theory_of_everything": "NOT_CLAIMED",
        },
        "original_six_q": list(SAMPLE_Q),
        "original_six_point_results_are_unchanged": True,
        "audio_generated": False,
    }
    artifacts = {
        "contract.json": canonical_json(contract),
        "pressure-pairs.csv": stream.getvalue().encode("ascii"),
        "sampling.json": canonical_json(sampled),
        "audit.json": canonical_json(audit),
    }
    impl = {p: sha256((root / p).read_bytes()) for p in IMPLEMENTATION_PATHS}
    manifest = {
        "profile": PROFILE, "version": VERSION,
        "parent_commit": PARENT_COMMIT, "parent_doi": PARENT_DOI,
        "parent_manifest_sha256": sha256(original["manifest.json"]),
        "parent_artifacts": {
            k: {"sha256": sha256(v), "bytes": len(v)} for k, v in sorted(original.items())
        },
        "source_sha256": SOURCE_SHA256,
        "implementation": impl,
        "outputs": {
            k: {"sha256": sha256(v), "bytes": len(v)} for k, v in sorted(artifacts.items())
        },
        "serialization": "ASCII sorted compact JSON LF; CSV LF; no audio",
        "manifest_self_hash": None, "canonical_pcm_sha256": None,
        "canonical_wav_sha256": None,
    }
    artifacts["manifest.json"] = canonical_json(manifest)
    return artifacts


def write_evidence(root: Path, destination: str, artifacts: dict[str, bytes]) -> Path:
    """Create exactly the allowed fresh directory, anchored to POSIX directory FDs."""
    path = PurePosixPath(destination)
    if (
        not destination or path.is_absolute() or "\\" in destination
        or any(part in {"", ".", ".."} for part in destination.split("/"))
    ):
        raise ValueError("destination must be a new relative directory without dot segments")
    if set(artifacts) != OUTPUT_NAMES or not all(
        name.endswith((".json", ".csv")) and "/" not in name for name in artifacts
    ):
        raise ValueError("invalid symbolic evidence artifact set")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptors = [os.open(root, flags)]
    try:
        for component in path.parts[:-1]:
            with suppress(FileExistsError):
                os.mkdir(component, mode=0o755, dir_fd=descriptors[-1])
            descriptors.append(os.open(component, flags, dir_fd=descriptors[-1]))
        parent = descriptors[-1]
        os.mkdir(path.parts[-1], mode=0o755, dir_fd=parent)
        descriptors.append(os.open(path.parts[-1], flags, dir_fd=parent))
        out = descriptors[-1]
        for name in sorted(artifacts):
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode=0o644, dir_fd=out,
            )
            with os.fdopen(fd, "wb") as handle:
                handle.write(artifacts[name])
        opened = os.fstat(out)
        visible = os.stat(path.parts[-1], dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISDIR(visible.st_mode) or (opened.st_dev, opened.st_ino) != (
            visible.st_dev, visible.st_ino
        ):
            raise ValueError("output directory changed during export")
    finally:
        for fd in reversed(descriptors):
            os.close(fd)
    return root / path
