"""Deterministic oversampled frequency-modulation synthesis."""

from __future__ import annotations

from numbers import Integral, Real

import numpy as np

from .base import (
    INSTRUMENT_ABI,
    IdentityDict,
    Instrument,
    MonoSignal,
    finite_float,
    integer,
    nonnegative_float,
    positive_float,
    unit_float,
    validate_mono_signal,
    validate_synthesis_request,
)
from .envelopes import ADSREnvelope
from .oscillators import decimate_fir, deterministic_phase


class FMSynth(Instrument):
    """An alias-reduced two-operator FM voice with bounded deviation.

    ``modulation_index`` is reduced only when necessary to keep the maximum
    instantaneous frequency below the internal Nyquist guard.  Oversampled
    renders are then low-pass filtered before deterministic decimation, reducing
    folded high-order sidebands while preserving an exact public sample count.
    """

    _FIR_TAPS_PER_PHASE = 16
    _MAX_INTERNAL_SAMPLES = 20_000_000

    def to_identity_dict(self) -> IdentityDict:
        """Return the full FM render identity for manifests and hashes."""

        return {
            "instrument_abi": INSTRUMENT_ABI,
            "implementation": "FMSynth.v1",
            "carrier_ratio": self.carrier_ratio,
            "modulator_ratio": self.modulator_ratio,
            "modulation_index": self.modulation_index,
            "modulation_sustain": self.modulation_sustain,
            "envelope": self.envelope.to_identity_dict(),
            "oversample": self.oversample,
            "guard_band": self.guard_band,
            "carrier_phase_radians": self.carrier_phase_radians,
            "modulator_phase_radians": self.modulator_phase_radians,
            "index_contour": "sustain_plus_sqrt_adsr.v1",
            "decimation_filter": "centered_blackman_sinc.v1",
            "fir_taps_per_phase": self._FIR_TAPS_PER_PHASE,
            "endpoint_zeroing": True,
            "seed_phase_source": "splitmix64-indexed-high53.v1",
        }

    def __init__(
        self,
        *,
        carrier_ratio: Real = 1.0,
        modulator_ratio: Real = 2.0,
        modulation_index: Real = 2.35,
        modulation_sustain: Real = 0.32,
        envelope: ADSREnvelope | None = None,
        oversample: Integral = 4,
        guard_band: Real = 0.90,
        carrier_phase_radians: Real | None = None,
        modulator_phase_radians: Real | None = None,
    ) -> None:
        self.carrier_ratio = positive_float("carrier_ratio", carrier_ratio)
        self.modulator_ratio = positive_float("modulator_ratio", modulator_ratio)
        self.modulation_index = nonnegative_float("modulation_index", modulation_index)
        self.modulation_sustain = unit_float("modulation_sustain", modulation_sustain)
        oversampling = integer("oversample", oversample)
        if oversampling not in (1, 2, 4, 8):
            raise ValueError("oversample must be one of 1, 2, 4, or 8")
        self.oversample = oversampling
        guard = unit_float("guard_band", guard_band)
        if guard <= 0.0:
            raise ValueError("guard_band must be greater than zero")
        self.guard_band = guard
        if envelope is not None and not isinstance(envelope, ADSREnvelope):
            raise TypeError("envelope must be an ADSREnvelope")
        self.envelope = (
            envelope
            if envelope is not None
            else ADSREnvelope(
                attack_seconds=0.004,
                decay_seconds=0.140,
                sustain_level=0.62,
                release_seconds=0.220,
                curve=1.8,
            )
        )
        self.carrier_phase_radians = (
            None
            if carrier_phase_radians is None
            else finite_float("carrier_phase_radians", carrier_phase_radians)
        )
        self.modulator_phase_radians = (
            None
            if modulator_phase_radians is None
            else finite_float("modulator_phase_radians", modulator_phase_radians)
        )

    def synthesize(
        self,
        *,
        frequency_hz: float,
        duration_seconds: float,
        velocity: float,
        sample_rate: int,
        seed: int,
    ) -> MonoSignal:
        """Render an oversampled, alias-reduced two-operator FM note."""

        frequency, gate_samples, level, rate, seed_value = validate_synthesis_request(
            frequency_hz=frequency_hz,
            duration_seconds=duration_seconds,
            velocity=velocity,
            sample_rate=sample_rate,
            seed=seed,
        )
        release_samples = self.envelope.release_sample_count(rate)
        target_samples = gate_samples + release_samples
        if level == 0.0:
            return np.zeros(target_samples, dtype=np.float64)

        carrier_frequency = frequency * self.carrier_ratio
        output_limit = 0.5 * rate * self.guard_band
        if carrier_frequency >= output_limit:
            return np.zeros(target_samples, dtype=np.float64)

        internal_rate = rate * self.oversample
        internal_gate = gate_samples * self.oversample
        internal_release = release_samples * self.oversample
        internal_samples = target_samples * self.oversample
        if internal_samples > self._MAX_INTERNAL_SAMPLES:
            raise ValueError(
                f"oversampled FM note requires {internal_samples} samples; "
                f"limit is {self._MAX_INTERNAL_SAMPLES}"
            )
        envelope = self.envelope.render_samples(
            internal_gate,
            internal_rate,
            release_samples=internal_release,
        )
        if envelope.size != internal_samples:
            raise AssertionError("oversampled envelope length contract was violated")

        modulator_frequency = frequency * self.modulator_ratio
        internal_limit = 0.5 * internal_rate * self.guard_band
        if modulator_frequency >= internal_limit or self.modulation_index == 0.0:
            bounded_index = 0.0
        else:
            maximum_index = max(0.0, (internal_limit - carrier_frequency) / modulator_frequency)
            bounded_index = min(self.modulation_index, maximum_index)

        carrier_phase = (
            deterministic_phase(seed_value, 0)
            if self.carrier_phase_radians is None
            else self.carrier_phase_radians
        )
        modulator_phase = (
            deterministic_phase(seed_value, 1)
            if self.modulator_phase_radians is None
            else self.modulator_phase_radians
        )
        time = np.arange(internal_samples, dtype=np.float64) / float(internal_rate)
        normalized_envelope = np.clip(envelope, 0.0, 1.0)
        index_contour = bounded_index * (
            self.modulation_sustain + (1.0 - self.modulation_sustain) * np.sqrt(normalized_envelope)
        )
        modulator = np.sin(2.0 * np.pi * modulator_frequency * time + modulator_phase)
        signal = np.sin(
            2.0 * np.pi * carrier_frequency * time + carrier_phase + index_contour * modulator
        )
        signal *= level * envelope

        if self.oversample > 1:
            signal = decimate_fir(
                signal,
                self.oversample,
                guard_band=self.guard_band,
                taps_per_phase=self._FIR_TAPS_PER_PHASE,
            )[:target_samples]
        signal = np.clip(signal, -level, level)
        signal[0] = 0.0
        signal[-1] = 0.0
        return validate_mono_signal(signal, expected_samples=target_samples)
