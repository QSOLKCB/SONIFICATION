"""Deterministic event rendering, mixing, and artifact assembly."""

from __future__ import annotations

import hashlib
import logging
import platform
import struct
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import numpy as np
from numpy.typing import NDArray

from . import __version__
from .composition import TrackSpec, build_phase1_tracks
from .config import LoopConfig
from .core.audio import encode_wav, normalize_peak, rational_soft_clip
from .core.provenance import build_fingerprint, build_manifest
from .core.synthesis import AdditiveSynth, FMSynth, Instrument, KarplusStrong
from .core.tuning import EqualTemperament

FloatArray = NDArray[np.float64]
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RenderResult:
    """In-memory output and provenance for one completed render."""

    config: LoopConfig
    audio: FloatArray
    pcm: NDArray[np.int32]
    pcm_bytes: bytes
    wav_bytes: bytes
    recipe: dict[str, Any]
    fingerprint: dict[str, Any]
    manifest: dict[str, Any]

    @property
    def wav_sha256(self) -> str:
        """Exact WAV identity from the manifest-bound fingerprint."""

        return str(self.manifest["fingerprint"]["wav_sha256"])


def _instrument(name: str) -> Instrument:
    instruments: dict[str, type[Instrument]] = {
        "additive": AdditiveSynth,
        "fm": FMSynth,
        "karplus": KarplusStrong,
    }
    try:
        return instruments[name]()
    except KeyError as error:
        raise ValueError(f"unknown instrument: {name}") from error


def _instrument_identity(instrument: Instrument) -> dict[str, Any]:
    identity = instrument.to_identity_dict()
    if not isinstance(identity, dict):
        raise TypeError("instrument identity must be a dictionary")
    return identity


def _derive_seed(global_seed: int, lane: int, event_index: int) -> int:
    """Derive a private unsigned 64-bit component seed with SHA-256."""

    preimage = b"SONIFICATION/COMPONENT-SEED/v1\0" + struct.pack(
        "<QII", global_seed, lane, event_index
    )
    return int.from_bytes(hashlib.sha256(preimage).digest()[:8], "little")


def _beat_to_frame(beat: float, total_beats: int, frame_count: int) -> int:
    exact = Decimal(str(beat)) * Decimal(frame_count) / Decimal(total_beats)
    return int(exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP)) % frame_count


def _add_circular(
    destination: FloatArray,
    signal: NDArray[np.floating],
    *,
    onset_frame: int,
    pan: float,
    gain: float,
) -> None:
    """Add a mono note and its release tail into a seamlessly repeating buffer."""

    mono = np.asarray(signal, dtype=np.float64)
    if mono.ndim != 1 or not np.all(np.isfinite(mono)):
        raise ValueError("instrument output must be a finite mono vector")
    angle = (pan + 1.0) * np.pi / 4.0
    gains = np.asarray((np.cos(angle), np.sin(angle)), dtype=np.float64) * gain
    frame_count = destination.shape[0]
    source_offset = 0
    write_offset = onset_frame
    while source_offset < mono.size:
        length = min(frame_count - write_offset, mono.size - source_offset)
        segment = mono[source_offset : source_offset + length]
        destination[write_offset : write_offset + length] += segment[:, np.newaxis] * gains
        source_offset += length
        write_offset = 0


def _runtime_identity() -> dict[str, Any]:
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "operating_system": platform.system(),
        "machine": platform.machine(),
        "byte_order": sys.byteorder,
        "float_mantissa_bits": sys.float_info.mant_dig,
    }


def _recipe(
    config: LoopConfig,
    tracks: tuple[TrackSpec, ...],
    instruments: dict[str, Instrument],
) -> dict[str, Any]:
    return {
        "schema": "sonification.render-recipe/v1",
        "application": {"name": "QSOL SONIFICATION", "version": __version__},
        "engine": {
            "id": "phase1_loop_composer",
            "version": "1.0.0",
            "dsp_abi": "sonification.float64-numpy/v1",
            "seed_derivation": "sha256-domain-first-64le/v1",
            "wav_writer": "riff-pcm-le/v1",
            "quantizer": "symmetric-half-away-from-zero/v1",
            "procedural_prng": {
                "algorithm": "splitmix64",
                "version": 1,
                "float_mapping": "high53/2^53",
            },
        },
        "determinism": {
            "mode": "replay_safe_float64",
            "runtime": _runtime_identity(),
            "hidden_entropy": False,
            "wall_clock_identity": False,
        },
        "render": {
            "config": config.to_identity_dict(),
            "master": {"soft_clip": "rational/v1", "drive": 1.15},
            "loop_tail_policy": "circular-fold/v1",
        },
        "tuning": {
            "system": "12tet",
            "reference_note": 69,
            "reference_hz": config.tuning_a4_hz,
        },
        "tracks": [
            {
                **track.to_identity_dict(),
                "instrument_contract": _instrument_identity(instruments[track.instrument]),
            }
            for track in tracks
        ],
        "mapping_boundary": (
            "Phase 1 uses explicit musical step patterns. Mathematical rhythm, E8, triality, "
            "Phi, Pi/2, and attractor bindings are reserved for separately versioned later phases."
        ),
    }


def render_loop(config: LoopConfig) -> RenderResult:
    """Render a complete deterministic musical loop and its provenance chain."""

    tracks = build_phase1_tracks(config)
    instruments = {track.instrument: _instrument(track.instrument) for track in tracks}
    recipe = _recipe(config, tracks, instruments)
    tuning = EqualTemperament(reference_hz=config.tuning_a4_hz)
    mix = np.zeros((config.frame_count, 2), dtype=np.float64)

    for track in tracks:
        LOGGER.debug("Rendering track %s with %d events", track.name, len(track.events))
        instrument = instruments[track.instrument]
        track_mix = np.zeros_like(mix)
        for event_index, event in enumerate(track.events):
            seed = _derive_seed(config.seed, track.seed_lane, event_index)
            note = instrument.synthesize(
                frequency_hz=tuning.frequency(event.note, event.cents_offset),
                duration_seconds=event.duration_beats * config.seconds_per_beat,
                velocity=event.velocity,
                sample_rate=config.sample_rate,
                seed=seed,
            )
            _add_circular(
                track_mix,
                note,
                onset_frame=_beat_to_frame(
                    event.onset_beats, config.total_beats, config.frame_count
                ),
                pan=event.pan,
                gain=track.gain,
            )
        mix += track_mix

    mastered = normalize_peak(rational_soft_clip(mix, drive=1.15), config.peak_dbfs)
    wav, pcm_bytes, pcm = encode_wav(mastered, config.sample_rate, config.bit_depth)
    fingerprint = build_fingerprint(
        pcm,
        pcm_bytes=pcm_bytes,
        wav_bytes=wav,
        sample_rate=config.sample_rate,
        bit_depth=config.bit_depth,
    )
    manifest = build_manifest(
        application_version=__version__,
        recipe=recipe,
        fingerprint=fingerprint,
        source_lineage=[
            {
                "relationship": "architectural-lineage",
                "project": "QSOLKCB/SPECTRAL",
                "note": (
                    "Domain-separated provenance and explicit claim boundaries are adapted "
                    "from SPECTRAL; this renderer is a fresh music-first implementation."
                ),
            }
        ],
    )
    # Protect identity-bearing sample arrays from accidental in-place mutation.
    # Callers that want to process a derivative can explicitly request a copy.
    mastered.setflags(write=False)
    pcm.setflags(write=False)
    return RenderResult(
        config=config,
        audio=mastered,
        pcm=pcm,
        pcm_bytes=pcm_bytes,
        wav_bytes=wav,
        recipe=recipe,
        fingerprint=fingerprint,
        manifest=manifest,
    )
