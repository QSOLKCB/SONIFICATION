"""Deterministic tuning helpers for musical event renderers."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real


@dataclass(frozen=True, slots=True)
class EqualTemperament:
    """Equal temperament with a configurable A4 reference and divisions."""

    reference_hz: float = 432.0
    reference_note: float = 69.0
    divisions: int = 12

    def __post_init__(self) -> None:
        for name in ("reference_hz", "reference_note"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a real number")
            normalized = float(value)
            if not math.isfinite(normalized):
                raise ValueError(f"{name} must be finite")
            object.__setattr__(self, name, 0.0 if normalized == 0.0 else normalized)
        if self.reference_hz <= 0.0:
            raise ValueError("reference_hz must be positive and finite")
        if isinstance(self.divisions, bool) or not isinstance(self.divisions, Integral):
            raise TypeError("divisions must be an integer")
        divisions = int(self.divisions)
        if not 1 <= divisions <= 240:
            raise ValueError("divisions must be between 1 and 240")
        object.__setattr__(self, "divisions", divisions)

    def frequency(self, note: float, cents_offset: float = 0.0) -> float:
        """Map a MIDI-style note plus cents offset to frequency in hertz."""

        for name, value in (("note", note), ("cents_offset", cents_offset)):
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a real number")
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite")
        note = float(note)
        cents_offset = float(cents_offset)
        steps = note - self.reference_note
        ratio = 2.0 ** (steps / self.divisions + cents_offset / 1_200.0)
        frequency_hz = self.reference_hz * ratio
        if frequency_hz <= 0.0 or not math.isfinite(frequency_hz):
            raise ValueError("calculated frequency is outside the finite positive domain")
        return frequency_hz


def midi_to_frequency(note: float, a4_hz: float = 432.0, cents_offset: float = 0.0) -> float:
    """Convenience wrapper for 12-tone equal temperament."""

    return EqualTemperament(reference_hz=a4_hz).frequency(note, cents_offset)
