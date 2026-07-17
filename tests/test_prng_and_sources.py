"""Golden-vector and sample-addressability tests for mathematical sources."""

from __future__ import annotations

import numpy as np
import pytest

from sonification.core.math import (
    ConstantSource,
    FractalNoiseSource,
    LogisticSource,
    SineSource,
    SplitMix64,
    splitmix64,
    splitmix64_array,
    splitmix64_at_indices,
    uint64_array_to_float64,
    uint64_to_float64,
)

# Published/reference SplitMix64 stream for an initial state of zero. These
# constants deliberately do not come from NumPy or from the implementation
# under test.
_ZERO_SEED_GOLDEN = np.asarray(
    [
        0xE220A8397B1DCDAF,
        0x6E789E6AA1B965F4,
        0x06C45D188009454F,
        0xF88BB8A8724C81EC,
        0x1B39896A51A8749B,
    ],
    dtype=np.uint64,
)


def test_splitmix64_reference_golden_vector() -> None:
    actual = splitmix64_array(0, _ZERO_SEED_GOLDEN.size)

    np.testing.assert_array_equal(actual, _ZERO_SEED_GOLDEN)
    assert splitmix64(0) == int(_ZERO_SEED_GOLDEN[0])


def test_splitmix64_scalar_vector_indexed_and_stateful_parity() -> None:
    seed = 0xFEDCBA9876543210
    expected = splitmix64_array(seed, 37)
    stream = SplitMix64(seed)

    assert [stream.uint64_at(index) for index in range(expected.size)] == expected.tolist()
    assert stream.state == seed
    np.testing.assert_array_equal(
        splitmix64_at_indices(seed, np.arange(expected.size, dtype=np.uint64)),
        expected,
    )
    assert [stream.next_uint64() for _ in range(expected.size)] == expected.tolist()


def test_splitmix64_vectors_are_stable_across_chunk_boundaries() -> None:
    seed = 0x0123456789ABCDEF
    full = splitmix64_array(seed, 41)
    indexed_chunks = np.concatenate(
        (
            splitmix64_array(seed, 7, start_index=0),
            splitmix64_array(seed, 13, start_index=7),
            splitmix64_array(seed, 21, start_index=20),
        )
    )
    stateful = SplitMix64(seed)
    stateful_chunks = np.concatenate((stateful.uint64(7), stateful.uint64(13), stateful.uint64(21)))

    np.testing.assert_array_equal(indexed_chunks, full)
    np.testing.assert_array_equal(stateful_chunks, full)


def test_splitmix64_float_scalar_vector_parity_and_bounds() -> None:
    words = splitmix64_array(2026, 64)
    vector = uint64_array_to_float64(words)
    scalar = np.asarray([uint64_to_float64(int(word)) for word in words])

    np.testing.assert_array_equal(vector, scalar)
    assert np.all(vector >= 0.0)
    assert np.all(vector < 1.0)


@pytest.mark.parametrize(
    "source",
    [
        ConstantSource(0.125),
        SineSource(
            frequency_hz=137.5,
            amplitude=0.7,
            phase_radians=0.23,
            offset=-0.1,
        ),
        LogisticSource(
            growth_rate=3.91,
            initial_state=0.412345,
            burn_in=11,
            amplitude=0.8,
        ),
        FractalNoiseSource(
            seed=0xA5A5,
            octaves=4,
            persistence=0.57,
            base_period_samples=3.5,
        ),
    ],
    ids=lambda source: type(source).__name__,
)
def test_math_sources_render_identically_whole_or_in_chunks(source: object) -> None:
    sample_rate = 8_000.0
    full = source.render(257, sample_rate)  # type: ignore[attr-defined]
    chunks = np.concatenate(
        [
            source.render(17, sample_rate, start_sample=0),  # type: ignore[attr-defined]
            source.render(36, sample_rate, start_sample=17),  # type: ignore[attr-defined]
            source.render(1, sample_rate, start_sample=53),  # type: ignore[attr-defined]
            source.render(203, sample_rate, start_sample=54),  # type: ignore[attr-defined]
        ]
    )

    assert full.dtype == np.float64
    assert full.flags.c_contiguous
    assert np.all(np.isfinite(full))
    np.testing.assert_array_equal(chunks, full)


def test_seeded_noise_source_is_repeatable_and_seed_sensitive() -> None:
    first = FractalNoiseSource(seed=100).render(128, 8_000)
    replay = FractalNoiseSource(seed=100).render(128, 8_000)
    changed = FractalNoiseSource(seed=101).render(128, 8_000)

    np.testing.assert_array_equal(first, replay)
    assert not np.array_equal(first, changed)
