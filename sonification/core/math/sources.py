"""Deterministic mathematical control and excitation sources."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral

import numpy as np

from .base import (
    FloatArray,
    MathSource,
    require_finite_real,
    require_non_negative_int,
)
from .constants import PHI, TAU
from .prng import (
    UINT64_MASK,
    splitmix64,
    splitmix64_at_indices,
    uint64_array_to_float64,
    validate_uint64,
)


@dataclass(frozen=True, slots=True)
class ConstantSource(MathSource):
    """Produce the same finite value at every absolute sample index."""

    value: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", require_finite_real(self.value, "value"))

    def _render(
        self,
        sample_count: int,
        sample_rate: float,
        start_sample: int,
    ) -> FloatArray:
        del sample_rate, start_sample
        return np.full(sample_count, self.value, dtype=np.float64)


@dataclass(frozen=True, slots=True)
class SineSource(MathSource):
    """Produce a sample-addressable sinusoid.

    The signal is ``offset + amplitude * sin(phase + 2*pi*f*n/sr)`` where
    ``n`` is the absolute sample index. Frequencies above Nyquist are allowed
    intentionally: this layer describes mathematical control sources, and a
    synthesis layer may choose to oversample or reject aliased audio carriers.
    """

    frequency_hz: float
    amplitude: float = 1.0
    phase_radians: float = 0.0
    offset: float = 0.0

    def __post_init__(self) -> None:
        frequency = require_finite_real(self.frequency_hz, "frequency_hz")
        if frequency < 0.0:
            raise ValueError("frequency_hz must be non-negative")
        object.__setattr__(self, "frequency_hz", frequency)
        object.__setattr__(self, "amplitude", require_finite_real(self.amplitude, "amplitude"))
        object.__setattr__(
            self,
            "phase_radians",
            require_finite_real(self.phase_radians, "phase_radians"),
        )
        object.__setattr__(self, "offset", require_finite_real(self.offset, "offset"))

    def _render(
        self,
        sample_count: int,
        sample_rate: float,
        start_sample: int,
    ) -> FloatArray:
        absolute_samples = np.arange(sample_count, dtype=np.float64)
        absolute_samples += float(start_sample)
        radians_per_sample = TAU * self.frequency_hz / sample_rate
        phase = np.remainder(
            self.phase_radians + radians_per_sample * absolute_samples,
            TAU,
        )
        return self.offset + self.amplitude * np.sin(phase)


@dataclass(frozen=True, slots=True)
class LogisticSource(MathSource):
    """Generate a deterministic logistic-map control stream.

    The recurrence is ``x[n+1] = growth_rate*x[n]*(1-x[n])``. The first
    returned value is the state *after* ``burn_in + start_sample`` updates.
    ``bipolar=True`` maps the unit-interval state through ``2*x - 1`` before
    applying amplitude and offset. Evaluation is deliberately scalar and in
    fixed order so replay does not depend on vectorized reduction behavior.
    """

    growth_rate: float = 3.99
    initial_state: float = 0.500_000_1
    burn_in: int = 64
    bipolar: bool = True
    amplitude: float = 1.0
    offset: float = 0.0

    def __post_init__(self) -> None:
        growth_rate = require_finite_real(self.growth_rate, "growth_rate")
        initial_state = require_finite_real(self.initial_state, "initial_state")
        if not 0.0 < growth_rate <= 4.0:
            raise ValueError("growth_rate must be in (0, 4]")
        if not 0.0 < initial_state < 1.0:
            raise ValueError("initial_state must be in (0, 1)")
        if not isinstance(self.bipolar, (bool, np.bool_)):
            raise TypeError("bipolar must be a boolean")
        object.__setattr__(self, "growth_rate", growth_rate)
        object.__setattr__(self, "initial_state", initial_state)
        object.__setattr__(self, "burn_in", require_non_negative_int(self.burn_in, "burn_in"))
        object.__setattr__(self, "bipolar", bool(self.bipolar))
        object.__setattr__(self, "amplitude", require_finite_real(self.amplitude, "amplitude"))
        object.__setattr__(self, "offset", require_finite_real(self.offset, "offset"))

    def _render(
        self,
        sample_count: int,
        sample_rate: float,
        start_sample: int,
    ) -> FloatArray:
        del sample_rate
        state = self.initial_state
        for _ in range(self.burn_in + start_sample):
            state = self.growth_rate * state * (1.0 - state)

        values = np.empty(sample_count, dtype=np.float64)
        if self.bipolar:
            for index in range(sample_count):
                values[index] = self.offset + self.amplitude * (2.0 * state - 1.0)
                state = self.growth_rate * state * (1.0 - state)
        else:
            for index in range(sample_count):
                values[index] = self.offset + self.amplitude * state
                state = self.growth_rate * state * (1.0 - state)
        return values


@dataclass(frozen=True, slots=True)
class FractalNoiseSource(MathSource):
    """Generate deterministic multi-scale value noise.

    Each octave hashes integer lattice points with SplitMix64, maps them to
    ``[-1, 1)``, and joins adjacent points with quintic smoothstep
    interpolation. Octave periods grow by ``lacunarity`` and amplitudes shrink
    by ``persistence``. A base period of one sample supplies a crisp procedural
    excitation; larger periods yield smooth modulation. The weighted sum is
    normalized, so ``amplitude`` has a stable meaning across octave counts.
    """

    seed: int
    octaves: int = 5
    persistence: float = 1.0 / PHI
    lacunarity: float = 2.0
    base_period_samples: float = 1.0
    amplitude: float = 1.0
    offset: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.octaves, (bool, np.bool_)) or not isinstance(self.octaves, Integral):
            raise TypeError("octaves must be an integer")
        octaves = int(self.octaves)
        if octaves < 1:
            raise ValueError("octaves must be at least 1")

        persistence = require_finite_real(self.persistence, "persistence")
        lacunarity = require_finite_real(self.lacunarity, "lacunarity")
        base_period = require_finite_real(self.base_period_samples, "base_period_samples")
        if not 0.0 < persistence <= 1.0:
            raise ValueError("persistence must be in (0, 1]")
        if lacunarity < 1.0:
            raise ValueError("lacunarity must be at least 1")
        if base_period <= 0.0:
            raise ValueError("base_period_samples must be positive")

        object.__setattr__(self, "seed", validate_uint64(self.seed))
        object.__setattr__(self, "octaves", octaves)
        object.__setattr__(self, "persistence", persistence)
        object.__setattr__(self, "lacunarity", lacunarity)
        object.__setattr__(self, "base_period_samples", base_period)
        object.__setattr__(self, "amplitude", require_finite_real(self.amplitude, "amplitude"))
        object.__setattr__(self, "offset", require_finite_real(self.offset, "offset"))

    @staticmethod
    def _fade(fraction: FloatArray) -> FloatArray:
        """Quintic smoothstep with zero first/second derivatives at endpoints."""

        return fraction * fraction * fraction * (fraction * (fraction * 6.0 - 15.0) + 10.0)

    @staticmethod
    def _lattice_values(seed: int, indices: np.ndarray) -> FloatArray:
        words = splitmix64_at_indices(seed, indices)
        return uint64_array_to_float64(words) * 2.0 - 1.0

    def _render(
        self,
        sample_count: int,
        sample_rate: float,
        start_sample: int,
    ) -> FloatArray:
        del sample_rate
        if sample_count == 0:
            return np.empty(0, dtype=np.float64)

        # float64 represents all realistic audio sample indices exactly. This
        # absolute coordinate is what makes sliced and full renders agree.
        absolute_samples = np.arange(sample_count, dtype=np.float64)
        absolute_samples += float(start_sample)
        result = np.zeros(sample_count, dtype=np.float64)
        weight = 1.0
        weight_sum = 0.0

        for octave in range(self.octaves):
            period = self.base_period_samples * (self.lacunarity**octave)
            if not math.isfinite(period):
                raise ValueError("octave period overflowed float64")
            coordinate = absolute_samples / period
            left_float = np.floor(coordinate)
            if left_float.size and float(left_float[-1]) > UINT64_MASK - 1:
                raise ValueError("fractal lattice index exceeds the uint64 domain")
            left = left_float.astype(np.uint64)
            right = left + np.uint64(1)
            fraction = coordinate - left_float
            fade = self._fade(fraction)

            octave_seed = splitmix64((self.seed + octave) & UINT64_MASK)
            left_values = self._lattice_values(octave_seed, left)
            right_values = self._lattice_values(octave_seed, right)
            octave_values = left_values + (right_values - left_values) * fade

            result += weight * octave_values
            weight_sum += weight
            weight *= self.persistence

        result /= weight_sum
        result *= self.amplitude
        result += self.offset
        return result


# A concise semantic alias for callers that do not need to expose the exact
# multi-scale construction in a UI label.
DeterministicNoiseSource = FractalNoiseSource
