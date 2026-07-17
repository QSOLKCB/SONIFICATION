"""Shared contracts and validation for procedural instruments.

The synthesis package deliberately owns no mutable global state. Every render is
fully described by the arguments to :meth:`Instrument.synthesize` plus the
instrument's current explicit configuration. Implementations never mutate that
configuration during rendering; callers should treat configured instruments as
immutable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from numbers import Integral, Real
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

from ..math import validate_uint64

MonoSignal = NDArray[np.float64]
JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
IdentityDict: TypeAlias = dict[str, JSONValue]

INSTRUMENT_ABI = "sonification.instrument.v1"
MAX_INSTRUMENT_SAMPLES = 10_000_000


def finite_float(name: str, value: Real) -> float:
    """Return *value* as a finite float or raise a descriptive exception."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def positive_float(name: str, value: Real) -> float:
    """Return a finite, strictly positive float."""

    result = finite_float(name, value)
    if result <= 0.0:
        raise ValueError(f"{name} must be greater than zero")
    return result


def nonnegative_float(name: str, value: Real) -> float:
    """Return a finite, non-negative float."""

    result = finite_float(name, value)
    if result < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return result


def unit_float(name: str, value: Real) -> float:
    """Return a finite float in the closed unit interval."""

    result = finite_float(name, value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1 inclusive")
    return result


def integer(name: str, value: Integral) -> int:
    """Return an integer while rejecting booleans and lossy coercions."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    return int(value)


def validate_sample_rate(sample_rate: Integral) -> int:
    """Validate a practical PCM sample rate.

    Rates from 8 kHz through 384 kHz cover standard audio workflows while
    catching common unit and argument-order mistakes early.
    """

    result = integer("sample_rate", sample_rate)
    if not 8_000 <= result <= 384_000:
        raise ValueError("sample_rate must be between 8000 and 384000 Hz")
    return result


def validate_processing_rate(sample_rate: Integral) -> int:
    """Validate an audio rate that may include up to 8x oversampling."""

    result = integer("sample_rate", sample_rate)
    if not 8_000 <= result <= 3_072_000:
        raise ValueError("processing sample_rate must be between 8000 and 3072000 Hz")
    return result


def seconds_to_samples(seconds: Real, sample_rate: Integral, *, name: str) -> int:
    """Convert seconds to the nearest integral sample count deterministically."""

    seconds_value = positive_float(name, seconds)
    rate = validate_sample_rate(sample_rate)
    count = round(seconds_value * rate)
    if count < 1:
        raise ValueError(f"{name} is shorter than one sample at {rate} Hz")
    if count > MAX_INSTRUMENT_SAMPLES:
        raise ValueError(f"{name} produces {count} samples; limit is {MAX_INSTRUMENT_SAMPLES}")
    return count


def validate_synthesis_request(
    *,
    frequency_hz: Real,
    duration_seconds: Real,
    velocity: Real,
    sample_rate: Integral,
    seed: Integral,
) -> tuple[float, int, float, int, int]:
    """Validate and normalize the common instrument render arguments.

    Returns:
        ``(frequency_hz, gate_samples, velocity, sample_rate, seed)``.
    """

    rate = validate_sample_rate(sample_rate)
    frequency = positive_float("frequency_hz", frequency_hz)
    if frequency >= 0.5 * rate:
        raise ValueError("frequency_hz must be below the Nyquist frequency")
    gate_samples = seconds_to_samples(duration_seconds, rate, name="duration_seconds")
    level = unit_float("velocity", velocity)
    seed_value = validate_uint64(integer("seed", seed))
    return frequency, gate_samples, level, rate, seed_value


def validate_mono_signal(signal: np.ndarray, *, expected_samples: int | None = None) -> MonoSignal:
    """Check the public signal contract and return a contiguous float64 array."""

    if not isinstance(signal, np.ndarray):
        raise TypeError("instrument output must be a numpy.ndarray")
    if signal.ndim != 1:
        raise ValueError("instrument output must be mono (one-dimensional)")
    if expected_samples is not None and signal.size != expected_samples:
        raise ValueError(
            f"instrument output has {signal.size} samples; expected {expected_samples}"
        )
    result = np.ascontiguousarray(signal, dtype=np.float64)
    if not np.all(np.isfinite(result)):
        raise FloatingPointError("instrument output contains non-finite values")
    return result


class Instrument(ABC):
    """Abstract, deterministic mono instrument.

    ``duration_seconds`` denotes gate duration.  Implementations append their
    configured release tail, so the returned array can be longer than
    ``round(duration_seconds * sample_rate)``.
    """

    @abstractmethod
    def synthesize(
        self,
        *,
        frequency_hz: float,
        duration_seconds: float,
        velocity: float,
        sample_rate: int,
        seed: int,
    ) -> MonoSignal:
        """Render a mono float64 note, including its release tail."""

    @abstractmethod
    def to_identity_dict(self) -> IdentityDict:
        """Return the complete JSON-safe configuration used for provenance."""
