"""Band-conscious oscillators and deterministic mathematical excitation."""

from __future__ import annotations

from numbers import Integral, Real

import numpy as np

from ..math import TAU, SplitMix64, validate_uint64
from .base import (
    MonoSignal,
    finite_float,
    integer,
    positive_float,
    unit_float,
    validate_mono_signal,
    validate_sample_rate,
)


def deterministic_unit(seed: Integral, stream: Integral = 0) -> float:
    """Map ``(seed, stream)`` to an exactly specified value in ``[0, 1)``."""

    seed_value = validate_uint64(integer("seed", seed))
    stream_value = validate_uint64(integer("stream", stream), "stream")
    return SplitMix64(seed_value).float64_at(stream_value)


def deterministic_phase(seed: Integral, stream: Integral = 0) -> float:
    """Return a replay-safe phase angle in ``[0, 2*pi)``."""

    return TAU * deterministic_unit(seed, stream)


def deterministic_excitation(length: Integral, seed: Integral) -> MonoSignal:
    """Generate a zero-mean, random-like deterministic excitation sequence.

    This is a sample-free integer hash construction, not ``numpy.random`` and
    not hidden global state.  Each raw sample is a direct function of its index
    and the supplied seed, making the requested burst stable under replay.
    """

    count = integer("length", length)
    if count < 1:
        raise ValueError("length must be at least one")
    seed_value = validate_uint64(integer("seed", seed))
    result = 2.0 * SplitMix64(seed_value).float64_vector(count) - 1.0
    result -= float(np.mean(result, dtype=np.float64))
    peak = float(np.max(np.abs(result)))
    if peak > 0.0:
        result /= peak
    return result


def sine_oscillator(
    *,
    frequency_hz: Real,
    sample_count: Integral,
    sample_rate: Integral,
    phase_radians: Real = 0.0,
) -> MonoSignal:
    """Render a pure sine oscillator below Nyquist."""

    frequency = positive_float("frequency_hz", frequency_hz)
    count = integer("sample_count", sample_count)
    if count < 0:
        raise ValueError("sample_count must be non-negative")
    rate = validate_sample_rate(sample_rate)
    if frequency >= 0.5 * rate:
        raise ValueError("frequency_hz must be below Nyquist")
    phase = finite_float("phase_radians", phase_radians)
    time = np.arange(count, dtype=np.float64) / float(rate)
    return np.sin(TAU * frequency * time + phase)


def band_limited_saw(
    *,
    frequency_hz: Real,
    sample_count: Integral,
    sample_rate: Integral,
    phase_radians: Real = 0.0,
    guard_band: Real = 0.94,
    max_harmonics: Integral = 256,
) -> MonoSignal:
    """Render a truncated Fourier saw without harmonics above the guard band."""

    frequency = positive_float("frequency_hz", frequency_hz)
    count = integer("sample_count", sample_count)
    if count < 0:
        raise ValueError("sample_count must be non-negative")
    rate = validate_sample_rate(sample_rate)
    phase = finite_float("phase_radians", phase_radians)
    guard = unit_float("guard_band", guard_band)
    if guard <= 0.0:
        raise ValueError("guard_band must be greater than zero")
    maximum = integer("max_harmonics", max_harmonics)
    if maximum < 1:
        raise ValueError("max_harmonics must be at least one")
    available = min(maximum, int(np.floor(0.5 * rate * guard / frequency)))
    if available < 1:
        return np.zeros(count, dtype=np.float64)
    time_phase = TAU * frequency * np.arange(count, dtype=np.float64) / rate
    result = np.zeros(count, dtype=np.float64)
    for harmonic in range(1, available + 1):
        result += ((-1.0) ** (harmonic + 1) / harmonic) * np.sin(harmonic * (time_phase + phase))
    result *= 2.0 / np.pi
    return validate_mono_signal(result, expected_samples=count)


def band_limited_square(
    *,
    frequency_hz: Real,
    sample_count: Integral,
    sample_rate: Integral,
    phase_radians: Real = 0.0,
    guard_band: Real = 0.94,
    max_harmonics: Integral = 255,
) -> MonoSignal:
    """Render an odd-harmonic square wave below a Nyquist guard band."""

    frequency = positive_float("frequency_hz", frequency_hz)
    count = integer("sample_count", sample_count)
    if count < 0:
        raise ValueError("sample_count must be non-negative")
    rate = validate_sample_rate(sample_rate)
    phase = finite_float("phase_radians", phase_radians)
    guard = unit_float("guard_band", guard_band)
    if guard <= 0.0:
        raise ValueError("guard_band must be greater than zero")
    maximum = integer("max_harmonics", max_harmonics)
    if maximum < 1:
        raise ValueError("max_harmonics must be at least one")
    highest = min(maximum, int(np.floor(0.5 * rate * guard / frequency)))
    time_phase = TAU * frequency * np.arange(count, dtype=np.float64) / rate
    result = np.zeros(count, dtype=np.float64)
    for harmonic in range(1, highest + 1, 2):
        result += np.sin(harmonic * (time_phase + phase)) / harmonic
    result *= 4.0 / np.pi
    return validate_mono_signal(result, expected_samples=count)


def decimate_fir(
    signal: np.ndarray,
    factor: Integral,
    *,
    guard_band: Real = 0.90,
    taps_per_phase: Integral = 16,
) -> MonoSignal:
    """Low-pass and decimate with a deterministic windowed-sinc FIR.

    The centered convolution has zero phase and a fixed, explicit kernel.  The
    returned length is ``ceil(len(signal) / factor)``.
    """

    source = validate_mono_signal(np.asarray(signal, dtype=np.float64))
    decimation = integer("factor", factor)
    if decimation < 1:
        raise ValueError("factor must be at least one")
    if decimation == 1:
        return source.copy()
    guard = unit_float("guard_band", guard_band)
    if guard <= 0.0:
        raise ValueError("guard_band must be greater than zero")
    per_phase = integer("taps_per_phase", taps_per_phase)
    if per_phase < 4:
        raise ValueError("taps_per_phase must be at least four")
    if source.size == 0:
        return source.copy()

    half = decimation * per_phase
    offsets = np.arange(-half, half + 1, dtype=np.float64)
    cutoff = 0.5 * guard / decimation
    kernel = 2.0 * cutoff * np.sinc(2.0 * cutoff * offsets)
    kernel *= np.blackman(kernel.size)
    kernel_sum = float(np.sum(kernel, dtype=np.float64))
    if abs(kernel_sum) <= np.finfo(np.float64).tiny:
        raise FloatingPointError("degenerate decimation filter")
    kernel /= kernel_sum

    full = np.convolve(source, kernel, mode="full")
    centered = full[half : half + source.size]
    return np.ascontiguousarray(centered[::decimation], dtype=np.float64)
