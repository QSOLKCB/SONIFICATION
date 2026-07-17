"""Validated note-event model."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from typing import Any


@dataclass(frozen=True, slots=True)
class NoteEvent:
    """One identity-bearing musical event measured in quarter-note beats."""

    onset_beats: float
    duration_beats: float
    note: float
    velocity: float = 1.0
    pan: float = 0.0
    cents_offset: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "onset_beats",
            "duration_beats",
            "note",
            "velocity",
            "pan",
            "cents_offset",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a real number")
            normalized = float(value)
            if not math.isfinite(normalized):
                raise ValueError(f"{name} must be finite")
            object.__setattr__(self, name, 0.0 if normalized == 0.0 else normalized)
        if self.onset_beats < 0.0:
            raise ValueError("onset_beats must be non-negative")
        if self.duration_beats <= 0.0:
            raise ValueError("duration_beats must be positive")
        if not 0.0 <= self.velocity <= 1.0:
            raise ValueError("velocity must be between 0 and 1")
        if not -1.0 <= self.pan <= 1.0:
            raise ValueError("pan must be between -1 and 1")
        if not -2_400.0 <= self.cents_offset <= 2_400.0:
            raise ValueError("cents_offset must be between -2400 and 2400")

    def to_identity_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation with a fixed field set."""

        return {
            "onset_beats": self.onset_beats,
            "duration_beats": self.duration_beats,
            "note": self.note,
            "velocity": self.velocity,
            "pan": self.pan,
            "cents_offset": self.cents_offset,
        }
