"""Bounded, offline helium adapter and symbolic receiver comparison.

SPDX-License-Identifier: MPL-2.0
Copyright (c) 2026 Trent Slade / QSOL-IMC.
No sampled audio is generated. Physical decimals are retained as strings;
exact arithmetic concerns their representations, not measurement certainty.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import struct
from collections import defaultdict
from contextlib import suppress
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
from pathlib import Path, PurePosixPath

from materials import __version__

SOURCE_PATH = "data/materials/helium4/DispersionAllPressures.txt"
SOURCE_SHA256 = "15a56ccdd2f681de0e1d3d1517dc4641732dbef4e2d6153591154cc4b039b50a"
SPEC_PATH = "spec/mat-spec-001.v1.json"
PROVENANCE_PATH = "data/materials/helium4/source.json"
SPEC_SHA256 = "65a59d918e3d2ab9d0a141f1fa7e2cda71b151e226617d81bc74768f70d963e7"
PROVENANCE_SHA256 = "6cd9e16d6f078e32ed87915d6a713fcab4b56b4e73891a95d0741fd8ea7c8dab"
IMPLEMENTATION_PATHS = (
    "materials/__init__.py",
    "materials/mat_spec.py",
    "scripts/build_mat_spec.py",
)
PRESSURES = ("0", "0.51", "1.02", "2.01", "5.01", "10.01", "24.08")
SAMPLE_Q = ("0.150", "0.500", "1.100", "1.600", "1.900", "2.100")
SCALE = Fraction(400)
MAX_INPUT_BYTES = 1_048_576
RUNTIME_NAMES = frozenset(
    {
        "contract.json",
        "observations.json",
        "events.csv",
        "audit.json",
        "rank.mid",
        "quantized.mid",
        "manifest.json",
    }
)


def canonical_json(value: object) -> bytes:
    """ASCII JSON, sorted keys, compact separators, one terminal LF; no NaN."""
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
        + "\n"
    ).encode("ascii")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_regular(path: Path, limit: int = MAX_INPUT_BYTES) -> bytes:
    """Open once, refuse special files/symlink leaves, and bound the actual read."""
    flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError("input must be a bounded regular file")
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("input exceeds byte limit")
    return raw


def parse_helium(raw: bytes) -> list[dict]:
    """Accept only the pinned, original author-supplied data bytes."""
    if sha256(raw) != SOURCE_SHA256:
        raise ValueError("helium source SHA-256 mismatch")
    rows = list(csv.reader(io.StringIO(raw.decode("utf-16")), delimiter="\t"))
    expected_headers = [
        ["wavevector"] + ["E", "errE"] * 7,
        ["A-1"] + ["meV"] * 14,
    ]
    if (
        len(rows) != 1053
        or any(len(row) != 16 for row in rows)
        or [row[1:] for row in rows[:2]] != expected_headers
    ):
        raise ValueError("unexpected helium table layout")
    pressure_header = [
        label for p in PRESSURES for label in (["P=0 bar"] * 2 if p == "0" else ["P=" + p] * 2)
    ]
    if rows[2][2:] != pressure_header:
        raise ValueError("unexpected helium pressure columns")
    observations = []
    for j, pressure in enumerate(PRESSURES):
        for index, row in enumerate(rows[3:]):
            q = row[1]
            if int(row[0]) != index + 1 or Fraction(q) != Fraction("0.150") + index * Fraction(
                "0.002"
            ):
                raise ValueError("unexpected helium wavevector grid")
            energy, error = row[2 + 2 * j : 4 + 2 * j]
            missing = energy == "NAN" and error == "NAN"
            if (energy == "NAN") != (error == "NAN"):
                raise ValueError("energy/error missingness differs")
            if not missing and (Fraction(energy) <= 0 or Fraction(error) <= 0):
                raise ValueError("non-positive measured energy/error")
            observations.append(
                {
                    "pressure_bar": pressure,
                    "q_inverse_angstrom": q,
                    "energy_meV": None if missing else energy,
                    "reported_energy_error_meV": None if missing else error,
                    "status": "missing" if missing else "tabulated",
                }
            )
    return observations


def rank_offsets(values: list[Fraction]) -> list[int]:
    """Equality/order only, dense ranks centered by floor(distinct_count/2)."""
    unique = sorted(set(values))
    ranks = {value: i - len(unique) // 2 for i, value in enumerate(unique)}
    return [ranks[value] for value in values]


def frequency_target(energy: Fraction, error: Fraction) -> tuple[Fraction, Fraction]:
    if energy < 0 or error < 0:
        raise ValueError("negative excitation energy or error")
    return energy * SCALE, error * SCALE


@lru_cache(maxsize=128)
def note_frequency(note: int) -> Decimal:
    with localcontext() as context:
        context.prec = 60
        return Decimal(440) * (Decimal(2).ln() * Decimal(note - 69) / 12).exp()


def nearest_midi(frequency: Fraction) -> int | None:
    """Exact threshold comparisons, nearest 12-TET, ties upward, no clamping.

    f=0 is explicitly unpitched. The frequency must otherwise lie between the
    reference frequencies of MIDI notes 0 and 127. Comparing 24th powers avoids
    a floating logarithm at half-semitone boundaries.
    """
    if frequency < 0:
        raise ValueError("negative frequency")
    if frequency == 0:
        return None
    power12 = (frequency / 440) ** 12
    if not Fraction(2) ** -69 <= power12 <= Fraction(2) ** 58:
        raise ValueError("frequency outside MIDI 0..127 reference range")
    power24 = power12 * power12
    low, high = 0, 127
    while low < high:
        middle = (low + high) // 2
        threshold = Fraction(2) ** (2 * middle + 1 - 138)
        if power24 < threshold:
            high = middle
        else:
            low = middle + 1
    return low


def cents_error(frequency: Fraction, note: int) -> str:
    with localcontext() as context:
        context.prec = 60
        target = Decimal(frequency.numerator) / Decimal(frequency.denominator)
        cents = 1200 * (note_frequency(note) / target).ln() / Decimal(2).ln()
        return format(cents.quantize(Decimal("0.000000001")), "f")


def map_observation(observation: dict) -> dict:
    mapped = dict(observation)
    if observation["status"] == "missing":
        mapped.update(
            frequency_Hz=None,
            frequency_error_Hz=None,
            midi_note=None,
            quantization_error_cents=None,
        )
        return mapped
    frequency, error = frequency_target(
        Fraction(observation["energy_meV"]), Fraction(observation["reported_energy_error_meV"])
    )
    note = nearest_midi(frequency)
    mapped.update(
        frequency_Hz=str(frequency),
        frequency_error_Hz=str(error),
        midi_note=note,
        quantization_error_cents=None if note is None else cents_error(frequency, note),
    )
    return mapped


def selected_events(observations: list[dict]) -> list[dict]:
    lookup = {(p["pressure_bar"], Fraction(p["q_inverse_angstrom"])): p for p in observations}
    events = []
    for j, pressure in enumerate(PRESSURES):
        selected = [lookup[pressure, Fraction(q)] for q in SAMPLE_Q]
        if any(p["status"] != "tabulated" for p in selected):
            raise ValueError("the six-sample comparison requires all selected observations")
        ranks = rank_offsets([Fraction(p["energy_meV"]) for p in selected])
        for i, (point, rank) in enumerate(zip(selected, ranks, strict=True)):
            events.append(
                {
                    **point,
                    "event_index": len(events),
                    "start_tick": (8 * j + i) * 240,
                    "duration_ticks": 180,
                    "channel": 0,
                    "velocity": 80,
                    "rank_offset": rank,
                    "rank_midi_note": None if point["midi_note"] is None else 60 + rank,
                }
            )
    return events


def midi_bytes(events: list[dict], note_key: str) -> bytes:
    """Standard MIDI format 0, no running status, fixed tempo, no synthesizer."""
    if note_key not in {"rank_midi_note", "midi_note"}:
        raise ValueError("unknown symbolic MIDI receiver")

    def vlq(value: int) -> bytes:
        if not 0 <= value <= 0x0FFFFFFF:
            raise ValueError("MIDI delta out of range")
        result = [value & 0x7F]
        while value > 127:
            value >>= 7
            result.insert(0, (value & 0x7F) | 0x80)
        return bytes(result)

    track = bytearray(b"\x00\xff\x51\x03\x07\xa1\x20")  # 500000 us/quarter.
    track.extend(b"\x00\xc0\x00")  # Program 0; its actual timbre is receiver-dependent.
    previous = 0
    for event in events:
        note = event[note_key]
        if note is None:  # Zero energy is unpitched; preserve timeline without a note-on.
            continue
        if not isinstance(note, int) or not 0 <= note <= 127:
            raise ValueError("invalid MIDI note")
        track.extend(vlq(event["start_tick"] - previous))
        track.extend(bytes((0x90, note, event["velocity"])))
        track.extend(vlq(event["duration_ticks"]))
        track.extend(bytes((0x80, note, 0)))
        previous = event["start_tick"] + event["duration_ticks"]
    track.extend(b"\x00\xff\x2f\x00")
    return (
        b"MThd"
        + struct.pack(">IHHH", 6, 0, 1, 480)
        + b"MTrk"
        + struct.pack(">I", len(track))
        + track
    )


def audit(observations: list[dict], events: list[dict]) -> dict:
    valid = [p for p in observations if p["status"] == "tabulated"]
    roundtrips = ratios = 0
    references = {}
    for point in valid:
        energy = Fraction(point["energy_meV"])
        error = Fraction(point["reported_energy_error_meV"])
        frequency = Fraction(point["frequency_Hz"])
        mapped_error = Fraction(point["frequency_error_Hz"])
        if frequency / SCALE != energy or mapped_error / SCALE != error:
            raise ValueError("linear receiver roundtrip failed")
        roundtrips += 1
        reference = references.setdefault(point["pressure_bar"], (energy, frequency))
        if energy / reference[0] != frequency / reference[1]:
            raise ValueError("linear receiver ratio preservation failed")
        ratios += 1
    groups = defaultdict(list)
    quantized_groups = defaultdict(list)
    order_comparisons = overlapping_intervals = scale_invariances = reverse_changes = 0
    for j, pressure in enumerate(PRESSURES):
        sample = events[j * 6 : (j + 1) * 6]
        energies = [Fraction(p["energy_meV"]) for p in sample]
        errors = [Fraction(p["reported_energy_error_meV"]) for p in sample]
        offsets = [p["rank_offset"] for p in sample]
        groups[tuple(offsets)].append(pressure)
        quantized_groups[tuple(p["midi_note"] for p in sample)].append(pressure)
        scaled = rank_offsets([2 * e for e in energies])
        if scaled != offsets:
            raise ValueError("positive scale control failed")
        scale_invariances += len(sample)
        reversed_offsets = rank_offsets(list(reversed(energies)))
        reverse_changes += sum(a != b for a, b in zip(offsets, reversed_offsets, strict=True))
        for a in range(6):
            for b in range(a + 1, 6):
                sign = lambda x: (x > 0) - (x < 0)  # noqa: E731
                if sign(energies[a] - energies[b]) != sign(offsets[a] - offsets[b]):
                    raise ValueError("rank equality/order preservation failed")
                order_comparisons += 1
                if abs(energies[a] - energies[b]) <= errors[a] + errors[b]:
                    overlapping_intervals += 1
    if (len(valid), len(observations) - len(valid)) != (7118, 232):
        raise ValueError("unexpected observation counts")
    with localcontext() as context:
        context.prec = 60
        phi = (1 + Decimal(5).sqrt()) / 2
        phi_cents = 1200 * phi.ln() / Decimal(2).ln()
        comparator = Fraction(8, 5)
        theoretical = {
            "status": "synthetic theoretical illustration; no cobalt-niobate observations",
            "phi_interval_cents": format(phi_cents.quantize(Decimal("0.000000001")), "f"),
            "phi_nearest_semitones_at_A440": nearest_midi(Fraction(phi) * 440) - 69,
            "phi_error_cents": format((800 - phi_cents).quantize(Decimal("0.000000001")), "f"),
            "comparator_ratio": "8/5",
            "comparator_nearest_semitones_at_A440": nearest_midi(comparator * 440) - 69,
            "interpretation": "different ratios can map to the same rank pair and MIDI interval",
        }
    return {
        "profile": "MAT-SPEC-001",
        "version": __version__,
        "valid_observations": len(valid),
        "missing_observations": 232,
        "exact_decimal_energy_and_error_roundtrips": roundtrips,
        "exact_ratios_to_within_pressure_reference": ratios,
        "selected_events_per_receiver": len(events),
        "selected_common_scale_contour_count": len(
            {
                tuple(p["frequency_Hz"] for p in events[j * 6 : (j + 1) * 6])
                for j in range(len(PRESSURES))
            }
        ),
        "selected_rank_order_and_equality_comparisons": order_comparisons,
        "selected_reported_error_interval_overlaps": overlapping_intervals,
        "interval_overlap_scope": (
            "reported +/-errE only; not a confidence statement or covariance model"
        ),
        "rank_contours": [{"offsets": list(k), "pressures_bar": v} for k, v in groups.items()],
        "quantized_contours": [
            {"notes": list(k), "pressures_bar": v} for k, v in quantized_groups.items()
        ],
        "rank_scope": "six specified wavevectors only; not a classification of full spectra",
        "maximum_absolute_quantization_error_cents": str(
            max(abs(Decimal(p["quantization_error_cents"])) for p in valid)
        ),
        "positive_energy_scale_control": {
            "factor": "2",
            "rank_offsets_unchanged": scale_invariances,
            "common_scale_targets_double": all(
                frequency_target(2 * Fraction(p["energy_meV"]), Fraction(0))[0]
                == 2 * Fraction(p["frequency_Hz"])
                for p in valid
            ),
        },
        "reverse_q_association_control": {
            "changed_selected_rank_offsets": reverse_changes,
            "preserves_energy_multiset": True,
            "scope": "reverse six selected energies at fixed q labels within each pressure",
        },
        "golden_ratio_control": theoretical,
        "listener_discrimination": "NOT_TESTED",
        "physical_phase_classification": "NOT_TESTED",
        "E8_symmetry_in_helium": "NOT_CLAIMED",
        "audio_generated": False,
    }


def build_bundle(
    root: Path, source: Path | None = None, *, render_audio: bool = False
) -> dict[str, bytes]:
    if render_audio:
        raise ValueError("rendered audio is explicitly disabled; symbolic outputs only")
    input_bytes = {
        SOURCE_PATH: read_regular(source if source is not None else root / SOURCE_PATH),
        SPEC_PATH: read_regular(root / SPEC_PATH),
        PROVENANCE_PATH: read_regular(root / PROVENANCE_PATH),
    }
    if (
        sha256(input_bytes[SPEC_PATH]) != SPEC_SHA256
        or sha256(input_bytes[PROVENANCE_PATH]) != PROVENANCE_SHA256
    ):
        raise ValueError("frozen MAT-SPEC-001 contract/provenance SHA-256 mismatch")
    contract = json.loads(input_bytes[SPEC_PATH])
    provenance = json.loads(input_bytes[PROVENANCE_PATH])
    # The contract is descriptive; version 1 has one frozen configuration.
    if (
        contract.get("profile") != "MAT-SPEC-001"
        or contract.get("version") != __version__
        or contract.get("energy_to_frequency_Hz_per_meV") != "400"
        or contract.get("selected_q_inverse_angstrom") != list(SAMPLE_Q)
        or contract.get("source_sha256") != SOURCE_SHA256
        or provenance.get("sha256") != SOURCE_SHA256
    ):
        raise ValueError("contract/source identity disagrees with MAT-SPEC-001 v1")
    observations = [map_observation(p) for p in parse_helium(input_bytes[SOURCE_PATH])]
    events = selected_events(observations)
    stream = io.StringIO(newline="")
    columns = list(events[0])
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(events)
    artifacts = {
        "contract.json": canonical_json(contract),
        "observations.json": canonical_json({"source": provenance, "observations": observations}),
        "events.csv": stream.getvalue().encode("ascii"),
        "audit.json": canonical_json(audit(observations, events)),
        "rank.mid": midi_bytes(events, "rank_midi_note"),
        "quantized.mid": midi_bytes(events, "midi_note"),
    }
    implementation = {p: sha256(read_regular(root / p)) for p in IMPLEMENTATION_PATHS}
    manifest = {
        "profile": "MAT-SPEC-001",
        "version": __version__,
        "doi": "10.5281/zenodo.24062652",
        "inputs": {p: {"sha256": sha256(raw), "bytes": len(raw)} for p, raw in input_bytes.items()},
        "implementation": {
            "files": implementation,
            "bundle_sha256": sha256(canonical_json(implementation)),
            "runtime": "Python >=3.11 standard library; POSIX filesystem export",
        },
        "outputs": {
            name: {"sha256": sha256(raw), "bytes": len(raw)} for name, raw in artifacts.items()
        },
        "canonical_serialization": "sorted ASCII JSON; compact separators; terminal LF; no NaN",
        "manifest_self_hash": "excluded; enclosing publication SHA256SUMS binds manifest.json",
        "canonical_pcm_sha256": None,
        "canonical_wav_sha256": None,
        "audio_status": "intentionally disabled",
    }
    artifacts["manifest.json"] = canonical_json(manifest)
    return artifacts


def write_bundle(root: Path, destination: str, artifacts: dict[str, bytes]) -> Path:
    """Create a fresh relative directory using anchored, no-follow POSIX FDs.

    Existing files/directories are never overwritten. A failure can leave a
    partial new directory; no unsafe path-based cleanup or retry is attempted.
    """
    path = PurePosixPath(destination)
    if (
        not destination
        or path.is_absolute()
        or "\\" in destination
        or any(p in {"", ".", ".."} for p in destination.split("/"))
    ):
        raise ValueError("output must be a new relative directory without dot segments")
    if set(artifacts) != RUNTIME_NAMES or any(
        PurePosixPath(name).name != name or Path(name).suffix not in {".mid", ".csv", ".json"}
        for name in artifacts
    ):
        raise ValueError("only the declared symbolic runtime artifacts are allowed")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fds = [os.open(root, flags)]
    try:
        for component in path.parts[:-1]:
            with suppress(FileExistsError):
                os.mkdir(component, mode=0o755, dir_fd=fds[-1])
            fds.append(os.open(component, flags, dir_fd=fds[-1]))
        parent_fd = fds[-1]
        leaf = path.parts[-1]
        os.mkdir(leaf, mode=0o755, dir_fd=parent_fd)
        out_fd = os.open(leaf, flags, dir_fd=parent_fd)
        fds.append(out_fd)
        for name, raw in artifacts.items():
            fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode=0o644,
                dir_fd=out_fd,
            )
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
        opened = os.fstat(out_fd)
        visible = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if (opened.st_dev, opened.st_ino) != (visible.st_dev, visible.st_ino):
            raise ValueError("output directory changed while writing")
    finally:
        for fd in reversed(fds):
            os.close(fd)
    return root / path
