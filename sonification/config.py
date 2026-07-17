"""Validated, identity-bearing render configuration."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal
from numbers import Integral, Real
from typing import Any

_MAX_SEED = (1 << 64) - 1
MAX_RENDER_FRAMES = 10_000_000


@dataclass(frozen=True, slots=True)
class LoopConfig:
    """Configuration for one deterministic loop render.

    The frame count is calculated with decimal half-up rounding so that loop
    duration does not depend on an intermediate binary floating-point value.
    """

    tempo_bpm: float = 128.0
    bars: int = 4
    beats_per_bar: int = 4
    sample_rate: int = 44_100
    bit_depth: int = 24
    tuning_a4_hz: float = 432.0
    seed: int = 2026
    peak_dbfs: float = -3.0
    voice_mode: str = "hybrid"

    def __post_init__(self) -> None:
        for name in ("bars", "beats_per_bar", "sample_rate", "bit_depth", "seed"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Integral):
                raise TypeError(f"{name} must be an integer")
            object.__setattr__(self, name, int(value))
        for name in ("tempo_bpm", "tuning_a4_hz", "peak_dbfs"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a real number")
            normalized = float(value)
            if not math.isfinite(normalized):
                raise ValueError(f"{name} must be finite")
            object.__setattr__(self, name, normalized)
        if not isinstance(self.voice_mode, str):
            raise TypeError("voice_mode must be a string")
        if not 20.0 <= self.tempo_bpm <= 400.0:
            raise ValueError("tempo_bpm must be between 20 and 400")
        if not 1 <= self.bars <= 64:
            raise ValueError("bars must be between 1 and 64")
        if not 1 <= self.beats_per_bar <= 16:
            raise ValueError("beats_per_bar must be between 1 and 16")
        if not 8_000 <= self.sample_rate <= 192_000:
            raise ValueError("sample_rate must be between 8000 and 192000")
        if self.bit_depth not in (16, 24):
            raise ValueError("bit_depth must be 16 or 24")
        if not 200.0 <= self.tuning_a4_hz <= 1_000.0:
            raise ValueError("tuning_a4_hz must be between 200 and 1000")
        if not 0 <= self.seed <= _MAX_SEED:
            raise ValueError("seed must be an unsigned 64-bit integer")
        if not -24.0 <= self.peak_dbfs <= -0.1:
            raise ValueError("peak_dbfs must be between -24.0 and -0.1")
        if self.voice_mode not in {"hybrid", "additive", "fm", "karplus"}:
            raise ValueError("voice_mode must be hybrid, additive, fm, or karplus")
        if self.frame_count > MAX_RENDER_FRAMES:
            raise ValueError(
                f"render requires {self.frame_count} frames; Phase 1 limit is {MAX_RENDER_FRAMES}"
            )

    @property
    def total_beats(self) -> int:
        """Number of quarter-note beats in the loop."""

        return self.bars * self.beats_per_bar

    @property
    def frame_count(self) -> int:
        """Exact integer number of frames selected for this loop."""

        numerator = Decimal(self.sample_rate) * Decimal(60) * Decimal(self.total_beats)
        frames = numerator / Decimal(str(self.tempo_bpm))
        return int(frames.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @property
    def duration_seconds(self) -> float:
        """Rendered duration implied by the integer frame count."""

        return self.frame_count / self.sample_rate

    @property
    def seconds_per_beat(self) -> float:
        """Seconds per quarter-note beat."""

        return 60.0 / self.tempo_bpm

    def to_identity_dict(self) -> dict[str, Any]:
        """Return canonicalizable identity fields, including derived length."""

        result = asdict(self)
        # Preserve all uint64 values across JSON implementations, including
        # browser runtimes whose exact integer range ends at 2**53 - 1.
        result["seed"] = f"0x{self.seed:016x}"
        result["total_beats"] = self.total_beats
        result["frame_count"] = self.frame_count
        return result
