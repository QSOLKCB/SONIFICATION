"""Determinism and signal-contract tests for the Phase 1 instruments."""

from __future__ import annotations

import numpy as np
import pytest

from sonification.core.synthesis import AdditiveSynth, FMSynth, KarplusStrong


@pytest.mark.parametrize(
    "instrument",
    [AdditiveSynth(), FMSynth(), KarplusStrong()],
    ids=lambda instrument: type(instrument).__name__,
)
def test_instrument_output_is_exactly_repeatable_finite_and_seed_sensitive(
    instrument: object,
) -> None:
    request = {
        "frequency_hz": 220.0,
        "duration_seconds": 0.025,
        "velocity": 0.7,
        "sample_rate": 8_000,
    }

    first = instrument.synthesize(**request, seed=0x1234)  # type: ignore[attr-defined]
    replay = instrument.synthesize(**request, seed=0x1234)  # type: ignore[attr-defined]
    changed = instrument.synthesize(**request, seed=0x1235)  # type: ignore[attr-defined]

    assert first.ndim == 1
    assert first.dtype == np.float64
    assert first.flags.c_contiguous
    assert first.size > round(request["duration_seconds"] * request["sample_rate"])
    assert np.all(np.isfinite(first))
    assert float(np.max(np.abs(first))) <= request["velocity"] + 1.0e-12
    assert np.any(first != 0.0)
    np.testing.assert_array_equal(first, replay)
    assert not np.array_equal(first, changed)


@pytest.mark.parametrize(
    "instrument",
    [AdditiveSynth(), FMSynth(), KarplusStrong()],
    ids=lambda instrument: type(instrument).__name__,
)
def test_zero_velocity_is_deterministic_silence(instrument: object) -> None:
    signal = instrument.synthesize(  # type: ignore[attr-defined]
        frequency_hz=220.0,
        duration_seconds=0.01,
        velocity=0.0,
        sample_rate=8_000,
        seed=999,
    )

    assert signal.dtype == np.float64
    assert signal.size > 80
    np.testing.assert_array_equal(signal, np.zeros_like(signal))


@pytest.mark.parametrize(
    "instrument",
    [AdditiveSynth(), FMSynth(), KarplusStrong()],
    ids=lambda instrument: type(instrument).__name__,
)
def test_instruments_reject_non_uint64_seed(instrument: object) -> None:
    with pytest.raises(ValueError):
        instrument.synthesize(  # type: ignore[attr-defined]
            frequency_hz=110.0,
            duration_seconds=0.01,
            velocity=0.5,
            sample_rate=8_000,
            seed=-1,
        )
