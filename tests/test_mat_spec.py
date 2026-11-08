"""Independent preservation, MIDI decoding, provenance and export-boundary checks.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

import csv
import io
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from materials.mat_spec import (
    IMPLEMENTATION_PATHS,
    RUNTIME_NAMES,
    SOURCE_PATH,
    build_bundle,
    frequency_target,
    map_observation,
    midi_bytes,
    nearest_midi,
    parse_helium,
    rank_offsets,
    read_regular,
    selected_events,
    sha256,
    write_bundle,
)

ROOT = Path(__file__).resolve().parents[1]


def decode_notes(raw: bytes) -> list[tuple[int, int, int, int]]:
    """Read SMF chunks/events independently of the writer; return (tick,status,note,velocity)."""
    if raw[:4] != b"MThd" or struct.unpack(">IHHH", raw[4:14]) != (6, 0, 1, 480):
        raise AssertionError("unexpected MIDI header")
    if raw[14:18] != b"MTrk" or struct.unpack(">I", raw[18:22])[0] != len(raw) - 22:
        raise AssertionError("bad MIDI chunk length")
    cursor, tick = 22, 0
    result = []

    def varlen() -> int:
        nonlocal cursor
        value = 0
        while True:
            byte = raw[cursor]
            cursor += 1
            value = 128 * value + (byte & 127)
            if byte < 128:
                return value

    while cursor < len(raw):
        tick += varlen()
        status = raw[cursor]
        cursor += 1
        if status == 0xFF:
            kind = raw[cursor]
            cursor += 1
            length = varlen()
            payload = raw[cursor : cursor + length]
            cursor += length
            if kind == 0x51 and payload != b"\x07\xa1\x20":
                raise AssertionError("incorrect tempo")
            if kind == 0x2F:
                if payload or cursor != len(raw):
                    raise AssertionError("incorrect MIDI end marker")
                return result
        elif status == 0xC0:
            if raw[cursor] != 0:
                raise AssertionError("incorrect program")
            cursor += 1
        elif status in {0x80, 0x90}:
            note, velocity = raw[cursor : cursor + 2]
            if note > 127 or velocity > 127:
                raise AssertionError("invalid data byte")
            result.append((tick, status, note, velocity))
            cursor += 2
        else:
            raise AssertionError("unexpected MIDI status")
    raise AssertionError("missing MIDI end marker")


class MatSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = build_bundle(ROOT)
        cls.audit = json.loads(cls.bundle["audit.json"])
        cls.observations = json.loads(cls.bundle["observations.json"])["observations"]
        cls.events = list(csv.DictReader(io.StringIO(cls.bundle["events.csv"].decode())))

    def test_attributed_observations_and_missing_data(self) -> None:
        self.assertEqual(len(self.observations), 7350)
        missing = [p for p in self.observations if p["status"] == "missing"]
        self.assertEqual(len(missing), 232)
        for point in missing:
            for key in ("energy_meV", "frequency_Hz", "midi_note", "quantization_error_cents"):
                self.assertIsNone(point[key])
        self.assertEqual(self.audit["exact_decimal_energy_and_error_roundtrips"], 7118)
        self.assertEqual(self.audit["exact_ratios_to_within_pressure_reference"], 7118)

    def test_ratio_error_and_order_properties(self) -> None:
        previous = None
        for point in sorted(
            (p for p in self.observations if p["status"] == "tabulated"),
            key=lambda p: Fraction(p["energy_meV"]),
        ):
            energy = Fraction(point["energy_meV"])
            frequency = Fraction(point["frequency_Hz"])
            self.assertEqual(frequency, 400 * energy)
            self.assertEqual(
                Fraction(point["frequency_error_Hz"]),
                400 * Fraction(point["reported_energy_error_meV"]),
            )
            self.assertLessEqual(abs(Decimal(point["quantization_error_cents"])), 50)
            if previous is not None:
                self.assertGreaterEqual(point["midi_note"], previous)
            previous = point["midi_note"]

    def test_rank_collisions_match_feasibility_result(self) -> None:
        self.assertEqual(self.audit["selected_common_scale_contour_count"], 7)
        self.assertEqual(len(self.audit["quantized_contours"]), 6)
        self.assertEqual(
            self.audit["rank_contours"],
            [
                {"offsets": [-3, -1, 2, 1, -2, 0], "pressures_bar": ["0", "0.51", "1.02", "2.01"]},
                {"offsets": [-3, 0, 2, 1, -2, -1], "pressures_bar": ["5.01", "10.01"]},
                {"offsets": [-3, 0, 2, 1, -1, -2], "pressures_bar": ["24.08"]},
            ],
        )
        self.assertEqual(self.audit["selected_rank_order_and_equality_comparisons"], 105)
        self.assertEqual(rank_offsets([Fraction(2), Fraction(2), Fraction(9)]), [-1, -1, 0])

    def test_quantization_known_references_and_information_loss(self) -> None:
        self.assertEqual(nearest_midi(Fraction(440)), 69)
        self.assertEqual(nearest_midi(Fraction(880)), 81)
        self.assertEqual(nearest_midi(Fraction(220)), 57)
        control = self.audit["golden_ratio_control"]
        self.assertEqual(control["phi_nearest_semitones_at_A440"], 8)
        self.assertEqual(control["comparator_nearest_semitones_at_A440"], 8)
        self.assertEqual(control["phi_error_cents"], "-33.090296357")
        for frequency in (Fraction(-1), Fraction(1), Fraction(20000)):
            with self.assertRaises(ValueError):
                nearest_midi(frequency)

    def test_zero_is_unpitched_and_distinct_from_missing(self) -> None:
        point = map_observation(
            {"status": "tabulated", "energy_meV": "0", "reported_energy_error_meV": "0.01"}
        )
        self.assertEqual(point["frequency_Hz"], "0")
        self.assertEqual(point["frequency_error_Hz"], "4")
        self.assertIsNone(point["midi_note"])
        self.assertIsNone(point["quantization_error_cents"])
        with self.assertRaises(ValueError):
            frequency_target(Fraction(-1), Fraction(0))
        synthetic = [dict(p) for p in self.observations]
        synthetic[0] = map_observation({**synthetic[0], "energy_meV": "0"})
        events = selected_events(synthetic)
        self.assertIsNone(events[0]["rank_midi_note"])
        for column in ("rank_midi_note", "midi_note"):
            self.assertEqual(len(decode_notes(midi_bytes(events, column))), 82)

    def test_independent_midi_decode_matches_csv_and_timeline(self) -> None:
        for filename, column in (("rank.mid", "rank_midi_note"), ("quantized.mid", "midi_note")):
            notes = decode_notes(self.bundle[filename])
            self.assertEqual(len(notes), 84)
            for event, on, off in zip(self.events, notes[::2], notes[1::2], strict=True):
                self.assertEqual(on, (int(event["start_tick"]), 0x90, int(event[column]), 80))
                self.assertEqual(off, (int(event["start_tick"]) + 180, 0x80, int(event[column]), 0))

    def test_provenance_binds_source_configuration_code_and_outputs(self) -> None:
        manifest = json.loads(self.bundle["manifest.json"])
        self.assertEqual(set(manifest["implementation"]["files"]), set(IMPLEMENTATION_PATHS))
        for path, expected in manifest["implementation"]["files"].items():
            self.assertEqual(sha256((ROOT / path).read_bytes()), expected)
        for path, receipt in manifest["inputs"].items():
            self.assertEqual(sha256((ROOT / path).read_bytes()), receipt["sha256"])
        for name, receipt in manifest["outputs"].items():
            self.assertEqual(sha256(self.bundle[name]), receipt["sha256"])
        self.assertIsNone(manifest["canonical_pcm_sha256"])
        self.assertIsNone(manifest["canonical_wav_sha256"])

    def test_reproducible_bytes(self) -> None:
        self.assertEqual(build_bundle(ROOT), self.bundle)

    def test_source_tampering_is_rejected(self) -> None:
        raw = (ROOT / SOURCE_PATH).read_bytes()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            parse_helium(raw[:-1] + bytes([raw[-1] ^ 1]))

    def test_contract_cannot_mislabel_units_or_receiver_settings(self) -> None:
        original_read = read_regular

        def changed_contract(path, limit=1_048_576):
            raw = original_read(path, limit)
            if path.name == "mat-spec-001.v1.json":
                return raw.replace(b'"energy": "meV"', b'"energy": "eV"')
            return raw

        with (
            patch("materials.mat_spec.read_regular", side_effect=changed_contract),
            self.assertRaisesRegex(ValueError, "contract/provenance"),
        ):
            build_bundle(ROOT)

    def test_bounded_regular_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            large = root / "large"
            large.write_bytes(b"x" * 9)
            with self.assertRaises(ValueError):
                read_regular(large, 8)
            link = root / "link"
            link.symlink_to(large)
            with self.assertRaises(OSError):
                read_regular(link)
            fifo = root / "fifo"
            os.mkfifo(fifo)
            with self.assertRaises(ValueError):
                read_regular(fifo)

    def test_audio_requests_fail_before_output(self) -> None:
        with self.assertRaisesRegex(ValueError, "audio"):
            build_bundle(ROOT, render_audio=True)
        for arguments in (["--render-audio"], ["--format", "wav"]):
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_mat_spec.py"), *arguments],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)

    def test_export_allowlist_no_overwrite_and_no_symlink_ancestors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = write_bundle(root, "dist/new", self.bundle)
            self.assertEqual({p.name for p in output.iterdir()}, RUNTIME_NAMES)
            with self.assertRaises(FileExistsError):
                write_bundle(root, "dist/new", self.bundle)
            outside = root / "outside"
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                write_bundle(root, "link/escape", self.bundle)
            self.assertEqual(list(outside.iterdir()), [])
            for destination in ("../escape", "/absolute", "a/../b", "", "a//b"):
                with self.assertRaises(ValueError):
                    write_bundle(root, destination, self.bundle)
            with self.assertRaises(ValueError):
                write_bundle(root, "disallowed", {"audio.wav": b""})

    def test_replaced_output_directory_cannot_redirect_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            real_open = os.open
            replaced = False

            def replacing_open(path, flags, *args, **kwargs):
                nonlocal replaced
                if path == "contract.json" and not replaced:
                    replaced = True
                    (root / "new").rename(root / "moved")
                    (root / "new").symlink_to(outside, target_is_directory=True)
                return real_open(path, flags, *args, **kwargs)

            with (
                patch("materials.mat_spec.os.open", side_effect=replacing_open),
                self.assertRaisesRegex(ValueError, "changed"),
            ):
                write_bundle(root, "new", self.bundle)
            self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
