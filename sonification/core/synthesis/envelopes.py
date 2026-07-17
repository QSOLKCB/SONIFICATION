"""Deterministic amplitude envelopes for procedural synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral, Real

import numpy as np

from .base import (
    IdentityDict,
    MonoSignal,
    integer,
    nonnegative_float,
    positive_float,
    seconds_to_samples,
    unit_float,
    validate_processing_rate,
    validate_sample_rate,
)


@dataclass(frozen=True, slots=True)
class ADSREnvelope:
    """A sample-accurate curved ADSR envelope.

    Attack and decay run while the note gate is open.  If the gate closes
    during either segment, release starts smoothly from the analytically
    evaluated gate-off level.  ``curve=1`` gives linear segments; larger values
    produce a slower attack and a faster perceptual decay/release.

    Args:
        attack_seconds: Time from silence to the peak.
        decay_seconds: Time from the peak to ``sustain_level``.
        sustain_level: Held amplitude in ``[0, 1]``.
        release_seconds: Tail duration after gate-off.
        curve: Positive power applied to each segment.
    """

    attack_seconds: float = 0.008
    decay_seconds: float = 0.090
    sustain_level: float = 0.72
    release_seconds: float = 0.180
    curve: float = 1.6

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "attack_seconds",
            nonnegative_float("attack_seconds", self.attack_seconds),
        )
        object.__setattr__(
            self,
            "decay_seconds",
            nonnegative_float("decay_seconds", self.decay_seconds),
        )
        object.__setattr__(self, "sustain_level", unit_float("sustain_level", self.sustain_level))
        object.__setattr__(
            self,
            "release_seconds",
            nonnegative_float("release_seconds", self.release_seconds),
        )
        object.__setattr__(self, "curve", positive_float("curve", self.curve))

    def release_sample_count(self, sample_rate: Integral) -> int:
        """Return the release length for ``sample_rate``."""

        rate = validate_processing_rate(sample_rate)
        if self.release_seconds == 0.0:
            return 0
        return round(self.release_seconds * rate)

    def to_identity_dict(self) -> IdentityDict:
        """Return all envelope parameters in canonical JSON-safe form."""

        return {
            "type": "ADSR",
            "attack_seconds": self.attack_seconds,
            "decay_seconds": self.decay_seconds,
            "sustain_level": self.sustain_level,
            "release_seconds": self.release_seconds,
            "curve": self.curve,
        }

    def _level(self, time_seconds: np.ndarray | float) -> np.ndarray:
        """Evaluate the pre-release envelope at non-negative times."""

        time = np.asarray(time_seconds, dtype=np.float64)
        if self.attack_seconds == 0.0:
            attack_level = np.ones_like(time)
        else:
            attack_progress = np.clip(time / self.attack_seconds, 0.0, 1.0)
            attack_level = np.power(attack_progress, self.curve)

        if self.decay_seconds == 0.0:
            post_attack = np.full_like(time, self.sustain_level)
        else:
            decay_progress = np.clip((time - self.attack_seconds) / self.decay_seconds, 0.0, 1.0)
            post_attack = self.sustain_level + (1.0 - self.sustain_level) * np.power(
                1.0 - decay_progress, self.curve
            )

        return np.where(time < self.attack_seconds, attack_level, post_attack)

    def render(self, duration_seconds: Real, sample_rate: Integral) -> MonoSignal:
        """Render a gate plus release tail as a mono float64 control signal."""

        gate_samples = seconds_to_samples(duration_seconds, sample_rate, name="duration_seconds")
        return self.render_samples(gate_samples, sample_rate)

    def render_samples(
        self,
        gate_samples: Integral,
        sample_rate: Integral,
        *,
        release_samples: Integral | None = None,
    ) -> MonoSignal:
        """Render from explicit counts, useful for deterministic oversampling."""

        rate = validate_processing_rate(sample_rate)
        gate_count = integer("gate_samples", gate_samples)
        if gate_count < 1:
            raise ValueError("gate_samples must be at least one")

        if release_samples is None:
            release_count = self.release_sample_count(rate)
        else:
            release_count = integer("release_samples", release_samples)
            if release_count < 0:
                raise ValueError("release_samples must be non-negative")

        gate_time = np.arange(gate_count, dtype=np.float64) / float(rate)
        gate = self._level(gate_time)
        if release_count == 0:
            return np.ascontiguousarray(gate, dtype=np.float64)

        gate_off_time = gate_count / float(rate)
        gate_off_level = float(self._level(gate_off_time))
        # Start one sample into the release so that its final sample is exactly
        # zero and the public array contains precisely ``release_count`` samples.
        release_progress = np.arange(1, release_count + 1, dtype=np.float64) / release_count
        release = gate_off_level * np.power(1.0 - release_progress, self.curve)
        return np.ascontiguousarray(np.concatenate((gate, release)), dtype=np.float64)


@dataclass(frozen=True, slots=True)
class PluckEnvelope:
    """Fast attack with a curved gate-off release for plucked models."""

    attack_seconds: float = 0.0015
    release_seconds: float = 0.240
    release_curve: float = 2.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "attack_seconds",
            nonnegative_float("attack_seconds", self.attack_seconds),
        )
        object.__setattr__(
            self,
            "release_seconds",
            nonnegative_float("release_seconds", self.release_seconds),
        )
        object.__setattr__(
            self,
            "release_curve",
            positive_float("release_curve", self.release_curve),
        )

    def release_sample_count(self, sample_rate: Integral) -> int:
        """Return the release length for ``sample_rate``."""

        rate = validate_sample_rate(sample_rate)
        return round(self.release_seconds * rate)

    def to_identity_dict(self) -> IdentityDict:
        """Return all envelope parameters in canonical JSON-safe form."""

        return {
            "type": "pluck",
            "attack_seconds": self.attack_seconds,
            "release_seconds": self.release_seconds,
            "release_curve": self.release_curve,
        }

    def render_samples(self, gate_samples: Integral, sample_rate: Integral) -> MonoSignal:
        """Render the pluck contour from an explicit gate length."""

        rate = validate_sample_rate(sample_rate)
        gate_count = integer("gate_samples", gate_samples)
        if gate_count < 1:
            raise ValueError("gate_samples must be at least one")
        release_count = self.release_sample_count(rate)

        gate_time = np.arange(gate_count, dtype=np.float64) / float(rate)
        if self.attack_seconds == 0.0:
            gate = np.ones(gate_count, dtype=np.float64)
            gate_off_level = 1.0
        else:
            gate = np.minimum(gate_time / self.attack_seconds, 1.0)
            gate_off_level = min(gate_count / (rate * self.attack_seconds), 1.0)

        if release_count == 0:
            return gate
        progress = np.arange(1, release_count + 1, dtype=np.float64) / release_count
        release = gate_off_level * np.power(1.0 - progress, self.release_curve)
        return np.ascontiguousarray(np.concatenate((gate, release)), dtype=np.float64)
