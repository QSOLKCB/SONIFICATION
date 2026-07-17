"""Deterministic, guard-banded additive synthesis."""

from __future__ import annotations

from collections.abc import Sequence
from numbers import Real

import numpy as np

from .base import (
    INSTRUMENT_ABI,
    IdentityDict,
    Instrument,
    MonoSignal,
    unit_float,
    validate_mono_signal,
    validate_synthesis_request,
)
from .envelopes import ADSREnvelope
from .oscillators import deterministic_phase


class AdditiveSynth(Instrument):
    """A musical additive voice with explicit anti-alias partial culling.

    Args:
        partial_ratios: Positive frequency multiples of the requested pitch.
        partial_amplitudes: Signed linear weights.  Defaults to a gently dark
            harmonic spectrum.
        partial_phases_radians: Optional fixed phases.  When omitted, phases are
            derived independently from ``seed`` for a reproducible organic
            onset.
        envelope: Note amplitude contour.
        guard_band: Fraction of Nyquist below which partials are retained.
    """

    _DEFAULT_RATIOS = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0)
    _DEFAULT_AMPLITUDES = (1.0, 0.46, 0.31, 0.19, 0.13, 0.09, 0.055)

    def to_identity_dict(self) -> IdentityDict:
        """Return the full additive render identity for manifests and hashes."""

        return {
            "instrument_abi": INSTRUMENT_ABI,
            "implementation": "AdditiveSynth.v1",
            "partial_ratios": list(self.partial_ratios),
            "partial_amplitudes": list(self.partial_amplitudes),
            "partial_phases_radians": (
                None if self.partial_phases_radians is None else list(self.partial_phases_radians)
            ),
            "envelope": self.envelope.to_identity_dict(),
            "guard_band": self.guard_band,
            "oscillator": "sine",
            "normalization": "sum_abs_retained_partial_amplitudes",
            "seed_phase_source": "splitmix64-indexed-high53.v1",
        }

    def __init__(
        self,
        *,
        partial_ratios: Sequence[Real] = _DEFAULT_RATIOS,
        partial_amplitudes: Sequence[Real] | None = None,
        partial_phases_radians: Sequence[Real] | None = None,
        envelope: ADSREnvelope | None = None,
        guard_band: Real = 0.94,
    ) -> None:
        ratios = np.asarray(tuple(partial_ratios), dtype=np.float64)
        if ratios.ndim != 1 or ratios.size == 0:
            raise ValueError("partial_ratios must be a non-empty one-dimensional sequence")
        if not np.all(np.isfinite(ratios)) or np.any(ratios <= 0.0):
            raise ValueError("partial_ratios must contain finite positive values")

        amplitude_source = (
            self._DEFAULT_AMPLITUDES
            if partial_amplitudes is None and ratios.size == len(self._DEFAULT_RATIOS)
            else partial_amplitudes
        )
        if amplitude_source is None:
            amplitude_source = tuple(1.0 / ratio for ratio in ratios)
        amplitudes = np.asarray(tuple(amplitude_source), dtype=np.float64)
        if amplitudes.ndim != 1 or amplitudes.size != ratios.size:
            raise ValueError("partial_amplitudes must match partial_ratios")
        if not np.all(np.isfinite(amplitudes)):
            raise ValueError("partial_amplitudes must be finite")
        if not np.any(amplitudes != 0.0):
            raise ValueError("at least one partial_amplitude must be non-zero")

        phases: np.ndarray | None
        if partial_phases_radians is None:
            phases = None
        else:
            phases = np.asarray(tuple(partial_phases_radians), dtype=np.float64)
            if phases.ndim != 1 or phases.size != ratios.size:
                raise ValueError("partial_phases_radians must match partial_ratios")
            if not np.all(np.isfinite(phases)):
                raise ValueError("partial_phases_radians must be finite")

        guard = unit_float("guard_band", guard_band)
        if guard <= 0.0:
            raise ValueError("guard_band must be greater than zero")
        if envelope is not None and not isinstance(envelope, ADSREnvelope):
            raise TypeError("envelope must be an ADSREnvelope")

        self.partial_ratios = tuple(float(value) for value in ratios)
        self.partial_amplitudes = tuple(float(value) for value in amplitudes)
        self.partial_phases_radians = (
            None if phases is None else tuple(float(value) for value in phases)
        )
        self.envelope = envelope if envelope is not None else ADSREnvelope()
        self.guard_band = guard

    def synthesize(
        self,
        *,
        frequency_hz: float,
        duration_seconds: float,
        velocity: float,
        sample_rate: int,
        seed: int,
    ) -> MonoSignal:
        """Render a harmonic note, dropping every unsafe partial."""

        frequency, gate_samples, level, rate, seed_value = validate_synthesis_request(
            frequency_hz=frequency_hz,
            duration_seconds=duration_seconds,
            velocity=velocity,
            sample_rate=sample_rate,
            seed=seed,
        )
        envelope = self.envelope.render_samples(gate_samples, rate)
        total_samples = envelope.size
        if level == 0.0:
            return np.zeros(total_samples, dtype=np.float64)

        safe_limit = 0.5 * rate * self.guard_band
        time = np.arange(total_samples, dtype=np.float64) / float(rate)
        result = np.zeros(total_samples, dtype=np.float64)
        retained_weight = 0.0

        for index, (ratio, amplitude) in enumerate(
            zip(self.partial_ratios, self.partial_amplitudes, strict=True)
        ):
            partial_frequency = frequency * ratio
            if amplitude == 0.0 or partial_frequency >= safe_limit:
                continue
            if self.partial_phases_radians is None:
                phase = deterministic_phase(seed_value, index)
            else:
                phase = self.partial_phases_radians[index]
            result += amplitude * np.sin(2.0 * np.pi * partial_frequency * time + phase)
            retained_weight += abs(amplitude)

        if retained_weight > 0.0:
            result *= (level / retained_weight) * envelope
        # No retained component is a valid, alias-safe silent render.
        return validate_mono_signal(result, expected_samples=total_samples)
