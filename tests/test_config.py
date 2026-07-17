"""Identity and duration tests for :mod:`sonification.config`."""

from __future__ import annotations

import pytest

from sonification.config import LoopConfig


@pytest.mark.parametrize(
    ("config", "expected_frames"),
    [
        (LoopConfig(), 330_750),
        (
            LoopConfig(
                tempo_bpm=24.0,
                bars=1,
                beats_per_bar=1,
                sample_rate=8_001,
            ),
            20_003,
        ),
        (
            LoopConfig(
                tempo_bpm=400.0,
                bars=1,
                beats_per_bar=1,
                sample_rate=8_000,
            ),
            1_200,
        ),
    ],
)
def test_frame_count_uses_decimal_half_up(config: LoopConfig, expected_frames: int) -> None:
    assert config.frame_count == expected_frames
    assert config.duration_seconds == expected_frames / config.sample_rate
    assert config.total_beats == config.bars * config.beats_per_bar


@pytest.mark.parametrize(
    ("seed", "expected_hex"),
    [
        (0, "0x0000000000000000"),
        ((1 << 53) + 123, "0x002000000000007b"),
        ((1 << 64) - 1, "0xffffffffffffffff"),
    ],
)
def test_seed_is_fixed_width_uint64_hex_in_identity(seed: int, expected_hex: str) -> None:
    identity = LoopConfig(seed=seed).to_identity_dict()

    assert identity["seed"] == expected_hex
    assert isinstance(identity["seed"], str)
    assert identity["frame_count"] == LoopConfig(seed=seed).frame_count
    assert identity["total_beats"] == LoopConfig(seed=seed).total_beats


@pytest.mark.parametrize("seed", [-1, 1 << 64, True, False, 1.5])
def test_seed_rejects_values_outside_integer_uint64_domain(seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        LoopConfig(seed=seed)  # type: ignore[arg-type]


def test_configuration_rejects_render_that_exceeds_memory_budget() -> None:
    with pytest.raises(ValueError, match="Phase 1 limit"):
        LoopConfig(
            tempo_bpm=20.0,
            bars=64,
            beats_per_bar=16,
            sample_rate=192_000,
        )
