"""Deterministic fractional-delay Karplus-Strong string synthesis."""

from __future__ import annotations

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
from .envelopes import PluckEnvelope
from .oscillators import deterministic_excitation, deterministic_phase


class KarplusStrong(Instrument):
    """A stable, tuned plucked-string model with deterministic excitation.

    The delay is fractional, and compensates approximately for the half-sample
    delay of the loop's two-point damping filter.  ``feedback`` is constrained
    below unity, guaranteeing that the recirculating loop cannot grow.

    Args:
        feedback: Per-period decay coefficient in ``[0, 1)``.
        brightness: Blend from two-point averaging (0) to an unfiltered loop
            (1).  Lower values lose high frequencies faster.
        pick_position: Fractional string position used for a comb-shaped pluck.
        excitation_tone: Amount of deterministic sinusoidal body mixed into the
            hash excitation.
        envelope: Gate/release contour applied after the physical decay.
    """

    _PICK_COMB_GAIN = 0.72
    _DC_BLOCK_COEFFICIENT = 0.995

    def to_identity_dict(self) -> IdentityDict:
        """Return the complete physical-model identity for provenance."""

        return {
            "instrument_abi": INSTRUMENT_ABI,
            "implementation": "KarplusStrong.v1",
            "feedback": self.feedback,
            "brightness": self.brightness,
            "pick_position": self.pick_position,
            "excitation_tone": self.excitation_tone,
            "envelope": self.envelope.to_identity_dict(),
            "excitation": "splitmix64-indexed-high53-zero-mean.v1",
            "fractional_delay": "linear-with-filter-delay-compensation.v1",
            "loop_filter": "brightness-weighted-two-point-average.v1",
            "pick_comb_gain": self._PICK_COMB_GAIN,
            "dc_block_coefficient": self._DC_BLOCK_COEFFICIENT,
        }

    def __init__(
        self,
        *,
        feedback: Real = 0.996,
        brightness: Real = 0.62,
        pick_position: Real = 0.19,
        excitation_tone: Real = 0.16,
        envelope: PluckEnvelope | None = None,
    ) -> None:
        feedback_value = unit_float("feedback", feedback)
        if feedback_value >= 1.0:
            raise ValueError("feedback must be strictly less than one")
        self.feedback = feedback_value
        self.brightness = unit_float("brightness", brightness)
        pick = unit_float("pick_position", pick_position)
        if pick <= 0.0 or pick >= 1.0:
            raise ValueError("pick_position must be strictly between zero and one")
        self.pick_position = pick
        self.excitation_tone = unit_float("excitation_tone", excitation_tone)
        if envelope is not None and not isinstance(envelope, PluckEnvelope):
            raise TypeError("envelope must be a PluckEnvelope")
        self.envelope = envelope if envelope is not None else PluckEnvelope()

    @staticmethod
    def _dc_block(signal: np.ndarray, coefficient: float = 0.995) -> MonoSignal:
        """Apply a stable first-order DC blocker."""

        result = np.empty_like(signal, dtype=np.float64)
        previous_input = 0.0
        previous_output = 0.0
        for index, sample in enumerate(signal):
            output = float(sample) - previous_input + coefficient * previous_output
            result[index] = output
            previous_input = float(sample)
            previous_output = output
        return result

    def synthesize(
        self,
        *,
        frequency_hz: float,
        duration_seconds: float,
        velocity: float,
        sample_rate: int,
        seed: int,
    ) -> MonoSignal:
        """Render a plucked string with a post-gate release tail."""

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

        # The averaging filter contributes between zero and half a sample of
        # phase delay.  Removing that estimate gives substantially better tuning.
        filter_delay = 0.5 * (1.0 - self.brightness)
        delay_samples = rate / frequency - filter_delay
        if not np.isfinite(delay_samples) or delay_samples > 1_000_000:
            raise ValueError("frequency_hz produces an impractically large delay line")
        if delay_samples < 2.0:
            raise ValueError(
                "frequency_hz is too high for the Karplus-Strong delay at this sample_rate"
            )

        initial_count = min(total_samples, max(2, int(np.ceil(delay_samples))))
        excitation = deterministic_excitation(initial_count, seed_value)

        # A pick-position comb creates the familiar spectral notch without any
        # stored sample.  The tone component lends a stable fundamental to very
        # short or bright notes.
        pick_delay = max(1, round(self.pick_position * delay_samples))
        combed = excitation - self._PICK_COMB_GAIN * np.roll(excitation, pick_delay % initial_count)
        phase = deterministic_phase(seed_value, 7)
        local_time = np.arange(initial_count, dtype=np.float64) / float(rate)
        tone = np.sin(2.0 * np.pi * frequency * local_time + phase)
        excitation = (1.0 - self.excitation_tone) * combed + self.excitation_tone * tone
        excitation -= float(np.mean(excitation, dtype=np.float64))
        excitation_peak = float(np.max(np.abs(excitation)))
        if excitation_peak > 0.0:
            excitation /= excitation_peak

        signal = np.zeros(total_samples, dtype=np.float64)
        signal[:initial_count] = excitation
        previous_delayed = 0.0
        for index in range(initial_count, total_samples):
            source_position = index - delay_samples
            lower = int(np.floor(source_position))
            fraction = source_position - lower
            delayed = (1.0 - fraction) * signal[lower] + fraction * signal[lower + 1]
            if index == initial_count:
                previous_position = source_position - 1.0
                previous_lower = max(0, int(np.floor(previous_position)))
                previous_fraction = max(0.0, previous_position - previous_lower)
                previous_upper = min(previous_lower + 1, index - 1)
                previous_delayed = (1.0 - previous_fraction) * signal[
                    previous_lower
                ] + previous_fraction * signal[previous_upper]
            damped = self.brightness * delayed + (1.0 - self.brightness) * 0.5 * (
                delayed + previous_delayed
            )
            signal[index] = self.feedback * damped
            previous_delayed = delayed

        signal = self._dc_block(signal, self._DC_BLOCK_COEFFICIENT)
        peak = float(np.max(np.abs(signal)))
        if peak > 0.0:
            signal /= peak
        signal *= level * envelope
        return validate_mono_signal(signal, expected_samples=total_samples)


# A descriptive alias for callers that consistently suffix instrument classes.
KarplusStrongSynth = KarplusStrong
