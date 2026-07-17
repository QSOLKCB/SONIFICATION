"""Replay-safe SplitMix64 pseudo-random number generation.

The implementation is deliberately independent of ``numpy.random``. A stream
is fully determined by one unsigned 64-bit seed and the SplitMix64 counter.
Stateless indexed methods make procedural noise sample-addressable, while the
stateful methods are convenient for synthesis algorithms that consume a
stream sequentially.
"""

from __future__ import annotations

from numbers import Integral
from typing import Final, overload

import numpy as np
from numpy.typing import ArrayLike, NDArray

UINT64_MASK: Final[int] = (1 << 64) - 1
GOLDEN_GAMMA: Final[int] = 0x9E3779B97F4A7C15
_MIX_MULTIPLIER_1: Final[int] = 0xBF58476D1CE4E5B9
_MIX_MULTIPLIER_2: Final[int] = 0x94D049BB133111EB
_UNIT_FLOAT_SCALE: Final[float] = 1.0 / (1 << 53)


UInt64Array = NDArray[np.uint64]
Float64Array = NDArray[np.float64]


def validate_uint64(value: int, name: str = "seed") -> int:
    """Validate an integer in the closed unsigned 64-bit domain."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(value)
    if not 0 <= normalized <= UINT64_MASK:
        raise ValueError(f"{name} must be in [0, 2**64 - 1]")
    return normalized


def _validate_size(size: int, name: str = "size") -> int:
    if isinstance(size, (bool, np.bool_)) or not isinstance(size, Integral):
        raise TypeError(f"{name} must be an integer")
    normalized = int(size)
    if normalized < 0:
        raise ValueError(f"{name} must be non-negative")
    return normalized


def _mix_word(word: int) -> int:
    """Apply the SplitMix64 finalizer to one already-advanced state word."""

    mixed = word & UINT64_MASK
    mixed = ((mixed ^ (mixed >> 30)) * _MIX_MULTIPLIER_1) & UINT64_MASK
    mixed = ((mixed ^ (mixed >> 27)) * _MIX_MULTIPLIER_2) & UINT64_MASK
    return (mixed ^ (mixed >> 31)) & UINT64_MASK


def _mix_words(words: UInt64Array) -> UInt64Array:
    """Vectorized SplitMix64 finalizer with explicit uint64 wraparound."""

    mixed = np.array(words, dtype=np.uint64, copy=True)
    with np.errstate(over="ignore"):
        mixed ^= mixed >> np.uint64(30)
        mixed *= np.uint64(_MIX_MULTIPLIER_1)
        mixed ^= mixed >> np.uint64(27)
        mixed *= np.uint64(_MIX_MULTIPLIER_2)
        mixed ^= mixed >> np.uint64(31)
    return mixed


def splitmix64(seed: int) -> int:
    """Return the first SplitMix64 output for ``seed``.

    This follows the reference transition exactly: add the golden-gamma
    increment modulo :math:`2^{64}`, then apply the SplitMix64 finalizer.
    """

    normalized_seed = validate_uint64(seed)
    return _mix_word((normalized_seed + GOLDEN_GAMMA) & UINT64_MASK)


def splitmix64_array(
    seed: int,
    size: int,
    start_index: int = 0,
) -> UInt64Array:
    """Return an indexed vector from the SplitMix64 stream.

    Args:
        seed: Unsigned 64-bit stream seed.
        size: Number of words to generate.
        start_index: Zero-based index of the first stream word.

    Returns:
        A one-dimensional NumPy array with dtype ``uint64``.
    """

    normalized_seed = validate_uint64(seed)
    normalized_size = _validate_size(size)
    normalized_start = validate_uint64(start_index, "start_index")
    if normalized_size and normalized_start + normalized_size - 1 > UINT64_MASK:
        raise ValueError("requested stream indices exceed the uint64 domain")
    if normalized_size == 0:
        return np.empty(0, dtype=np.uint64)

    with np.errstate(over="ignore"):
        counters = np.arange(normalized_size, dtype=np.uint64)
        counters += np.uint64((normalized_start + 1) & UINT64_MASK)
        states = np.uint64(normalized_seed) + np.uint64(GOLDEN_GAMMA) * counters
    return _mix_words(states)


def splitmix64_at_indices(seed: int, indices: ArrayLike) -> UInt64Array:
    """Return SplitMix64 words at arbitrary zero-based stream indices."""

    normalized_seed = validate_uint64(seed)
    raw_indices = np.asarray(indices)
    if raw_indices.dtype.kind not in {"i", "u"}:
        raise TypeError("indices must contain integers")
    if raw_indices.dtype.kind == "i" and np.any(raw_indices < 0):
        raise ValueError("indices must be non-negative")
    unsigned_indices = raw_indices.astype(np.uint64, copy=False)
    with np.errstate(over="ignore"):
        states = np.uint64(normalized_seed) + np.uint64(GOLDEN_GAMMA) * (
            unsigned_indices + np.uint64(1)
        )
    return _mix_words(states)


def uint64_to_float64(value: int) -> float:
    """Map one unsigned 64-bit word uniformly to the half-open interval [0, 1)."""

    normalized = validate_uint64(value, "value")
    return float(normalized >> 11) * _UNIT_FLOAT_SCALE


def uint64_array_to_float64(values: ArrayLike) -> Float64Array:
    """Map unsigned 64-bit words to binary64 values in ``[0.0, 1.0)``."""

    raw_values = np.asarray(values)
    if raw_values.dtype.kind not in {"i", "u"}:
        raise TypeError("values must contain integers")
    if raw_values.dtype.kind == "i" and np.any(raw_values < 0):
        raise ValueError("values must be non-negative")
    words = raw_values.astype(np.uint64, copy=False)
    return ((words >> np.uint64(11)).astype(np.float64)) * _UNIT_FLOAT_SCALE


class SplitMix64:
    """A small deterministic SplitMix64 stream with indexed random access.

    Stateful methods mutate only the local counter state. Indexed methods are
    pure functions of the original seed and index, and do not advance the
    sequential stream.
    """

    __slots__ = ("_seed", "_state")

    def __init__(self, seed: int) -> None:
        """Initialize a stream from one unsigned 64-bit seed."""

        self._seed = validate_uint64(seed)
        self._state = self._seed

    @property
    def seed(self) -> int:
        """The immutable seed from which this stream was constructed."""

        return self._seed

    @property
    def state(self) -> int:
        """The current sequential counter state as an unsigned 64-bit word."""

        return self._state

    def reset(self) -> None:
        """Reset the sequential stream to its initial seed."""

        self._state = self._seed

    def next_uint64(self) -> int:
        """Advance and return one unsigned 64-bit output word."""

        self._state = (self._state + GOLDEN_GAMMA) & UINT64_MASK
        return _mix_word(self._state)

    def next_float64(self) -> float:
        """Advance and return one binary64 value in ``[0.0, 1.0)``."""

        return uint64_to_float64(self.next_uint64())

    @overload
    def uint64(self, size: None = None) -> int: ...

    @overload
    def uint64(self, size: int) -> UInt64Array: ...

    def uint64(self, size: int | None = None) -> int | UInt64Array:
        """Return and consume one word or a vector of words."""

        if size is None:
            return self.next_uint64()
        normalized_size = _validate_size(size)
        words = splitmix64_array(self._state, normalized_size)
        self._state = (self._state + GOLDEN_GAMMA * normalized_size) & UINT64_MASK
        return words

    @overload
    def random(self, size: None = None) -> float: ...

    @overload
    def random(self, size: int) -> Float64Array: ...

    def random(self, size: int | None = None) -> float | Float64Array:
        """Return and consume one value or a vector in ``[0.0, 1.0)``."""

        if size is None:
            return self.next_float64()
        return uint64_array_to_float64(self.uint64(size))

    def uint64_at(self, index: int) -> int:
        """Return one word at ``index`` without advancing this stream."""

        normalized_index = validate_uint64(index, "index")
        state = (self._seed + GOLDEN_GAMMA * (normalized_index + 1)) & UINT64_MASK
        return _mix_word(state)

    def float64_at(self, index: int) -> float:
        """Return one unit-interval value at ``index`` without advancing."""

        return uint64_to_float64(self.uint64_at(index))

    def uint64_vector(self, size: int, start_index: int = 0) -> UInt64Array:
        """Return indexed words without advancing the sequential stream."""

        return splitmix64_array(self._seed, size, start_index)

    def float64_vector(self, size: int, start_index: int = 0) -> Float64Array:
        """Return indexed unit-interval values without advancing the stream."""

        return uint64_array_to_float64(self.uint64_vector(size, start_index))
