"""Abstract contracts and validation for sample-addressable math sources."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from numbers import Integral, Real

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
"""A one-dimensional NumPy array containing binary64 samples."""


def validate_render_request(
    sample_count: int,
    sample_rate: float,
    start_sample: int = 0,
) -> tuple[int, float, int]:
    """Validate and normalize the common render arguments.

    Args:
        sample_count: Number of samples to produce. Zero is valid.
        sample_rate: Positive sampling frequency in hertz.
        start_sample: Non-negative absolute sample offset. Sources must use
            this offset so that rendering in chunks reproduces a full render.

    Returns:
        The normalized ``(sample_count, sample_rate, start_sample)`` tuple.

    Raises:
        TypeError: If an argument has the wrong scalar type.
        ValueError: If an argument is outside its valid domain.
    """

    if isinstance(sample_count, (bool, np.bool_)) or not isinstance(sample_count, Integral):
        raise TypeError("sample_count must be an integer")
    if isinstance(start_sample, (bool, np.bool_)) or not isinstance(start_sample, Integral):
        raise TypeError("start_sample must be an integer")
    if isinstance(sample_rate, (bool, np.bool_)) or not isinstance(sample_rate, Real):
        raise TypeError("sample_rate must be a real number")

    normalized_count = int(sample_count)
    normalized_start = int(start_sample)
    normalized_rate = float(sample_rate)

    if normalized_count < 0:
        raise ValueError("sample_count must be non-negative")
    if normalized_start < 0:
        raise ValueError("start_sample must be non-negative")
    if not math.isfinite(normalized_rate) or normalized_rate <= 0.0:
        raise ValueError("sample_rate must be finite and positive")

    return normalized_count, normalized_rate, normalized_start


def require_finite_real(value: float, name: str) -> float:
    """Return ``value`` as ``float`` after strict finite-real validation."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def require_non_negative_int(value: int, name: str) -> int:
    """Return ``value`` as ``int`` after non-negative-integer validation."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if normalized < 0:
        raise ValueError(f"{name} must be non-negative")
    return normalized


class MathSource(ABC):
    """Abstract base class for deterministic mathematical sample sources.

    ``MathSource`` uses absolute sample addressing. Given equal construction
    parameters, ``render(n, sr, start)`` must not depend on previous calls or
    mutable global state. Consequently, adjacent chunks can be concatenated
    into the same signal as a single full render (subject only to documented
    floating-point semantics).

    Subclasses implement :meth:`_render`; this public template method enforces
    the common argument and output contracts.
    """

    def render(
        self,
        sample_count: int,
        sample_rate: float,
        start_sample: int = 0,
    ) -> FloatArray:
        """Render a one-dimensional deterministic ``float64`` signal.

        Args:
            sample_count: Number of samples to return. Zero returns an empty
                array without special-casing in callers.
            sample_rate: Positive sampling frequency in hertz.
            start_sample: Absolute sample index of the first returned value.

        Returns:
            A finite, one-dimensional NumPy ``float64`` array with exactly
            ``sample_count`` entries.

        Raises:
            TypeError: If render arguments have invalid scalar types.
            ValueError: If render arguments or generated samples violate the
                source contract.
        """

        count, rate, start = validate_render_request(sample_count, sample_rate, start_sample)
        rendered = np.asarray(self._render(count, rate, start), dtype=np.float64)

        if rendered.ndim != 1 or rendered.shape != (count,):
            raise ValueError(
                f"{type(self).__name__} returned shape {rendered.shape}; expected ({count},)"
            )
        if not np.all(np.isfinite(rendered)):
            raise ValueError(f"{type(self).__name__} generated non-finite samples")

        return np.ascontiguousarray(rendered, dtype=np.float64)

    @abstractmethod
    def _render(
        self,
        sample_count: int,
        sample_rate: float,
        start_sample: int,
    ) -> FloatArray:
        """Implement a validated render request for a concrete source."""
