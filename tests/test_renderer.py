"""End-to-end deterministic renderer tests without version-specific WAV goldens."""

from __future__ import annotations

import hashlib

import numpy as np

from sonification.config import LoopConfig
from sonification.renderer import render_loop


def _short_config(seed: int = 2026) -> LoopConfig:
    return LoopConfig(
        tempo_bpm=400.0,
        bars=1,
        beats_per_bar=1,
        sample_rate=8_000,
        bit_depth=16,
        seed=seed,
        voice_mode="hybrid",
    )


def test_renderer_is_bit_exact_on_immediate_replay() -> None:
    config = _short_config()

    first = render_loop(config)
    replay = render_loop(config)

    assert first.audio.shape == (config.frame_count, 2)
    assert first.pcm.shape == (config.frame_count, 2)
    assert first.audio.dtype == np.float64
    assert first.pcm.dtype == np.int32
    assert np.all(np.isfinite(first.audio))
    np.testing.assert_array_equal(first.audio, replay.audio)
    np.testing.assert_array_equal(first.pcm, replay.pcm)
    assert first.pcm_bytes == replay.pcm_bytes
    assert first.wav_bytes == replay.wav_bytes
    assert first.recipe == replay.recipe
    assert first.fingerprint == replay.fingerprint
    assert first.manifest == replay.manifest
    assert first.wav_sha256 == hashlib.sha256(first.wav_bytes).hexdigest()
    assert first.fingerprint["pcm_sha256"] == hashlib.sha256(first.pcm_bytes).hexdigest()
    assert not first.audio.flags.writeable
    assert not first.pcm.flags.writeable
    assert first.recipe is not first.manifest["recipe"]
    assert first.fingerprint is not first.manifest["fingerprint"]


def test_renderer_seed_changes_audio_without_changing_length_contract() -> None:
    first = render_loop(_short_config(seed=11))
    changed = render_loop(_short_config(seed=12))

    assert first.pcm.shape == changed.pcm.shape
    assert len(first.wav_bytes) == len(changed.wav_bytes)
    assert first.wav_bytes != changed.wav_bytes
    assert first.wav_sha256 != changed.wav_sha256
