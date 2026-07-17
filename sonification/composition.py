"""Phase 1 musical plan expressed as deterministic event tracks."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any

from .config import LoopConfig
from .core.sequencing import NoteEvent, events_from_steps


@dataclass(frozen=True, slots=True)
class TrackSpec:
    """One instrument assignment, event sequence, and mix gain."""

    name: str
    instrument: str
    events: tuple[NoteEvent, ...]
    gain: float
    seed_lane: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("track name must not be empty")
        object.__setattr__(self, "name", self.name.strip())
        if not isinstance(self.instrument, str):
            raise TypeError("instrument must be a string")
        if self.instrument not in {"additive", "fm", "karplus"}:
            raise ValueError("unknown Phase 1 instrument")
        events = tuple(self.events)
        if not events or not all(isinstance(event, NoteEvent) for event in events):
            raise ValueError("track must contain at least one event")
        object.__setattr__(self, "events", events)
        if isinstance(self.gain, bool) or not isinstance(self.gain, Real):
            raise TypeError("track gain must be a real number")
        gain = float(self.gain)
        if not math.isfinite(gain) or not 0.0 < gain <= 2.0:
            raise ValueError("track gain must be finite and in (0, 2]")
        object.__setattr__(self, "gain", gain)
        if isinstance(self.seed_lane, bool) or not isinstance(self.seed_lane, Integral):
            raise TypeError("seed_lane must be an integer")
        lane = int(self.seed_lane)
        if not 0 <= lane <= 0xFFFFFFFF:
            raise ValueError("seed_lane must be an unsigned 32-bit integer")
        object.__setattr__(self, "seed_lane", lane)

    def to_identity_dict(self) -> dict[str, Any]:
        """Return the complete identity-bearing track plan."""

        return {
            "name": self.name,
            "instrument": self.instrument,
            "gain": self.gain,
            "seed_lane": self.seed_lane,
            "events": [event.to_identity_dict() for event in self.events],
        }


def _bounded(events: tuple[NoteEvent, ...], total_beats: int) -> tuple[NoteEvent, ...]:
    return tuple(event for event in events if event.onset_beats < total_beats)


def build_phase1_tracks(config: LoopConfig) -> tuple[TrackSpec, ...]:
    """Build an immediately musical dark-electro loop for the selected voice mode.

    The patterns are intentionally explicit in Phase 1. Later mathematical
    rhythm generators will produce the same ``NoteEvent`` contract.
    """

    repeats = math.ceil(config.total_beats / 4.0)
    bass = _bounded(
        events_from_steps(
            (0, None, 0, 3, 0, None, 5, 7),
            root_note=33.0,
            step_beats=0.5,
            duration_beats=0.44,
            velocity_pattern=(0.94, 0.66, 0.78, 0.70, 0.88, 0.62, 0.80, 0.74),
            pan_pattern=(-0.08, 0.04, 0.08, -0.04),
            repeats=repeats,
        ),
        config.total_beats,
    )
    glass = _bounded(
        events_from_steps(
            (0, 7, 3, 10),
            root_note=57.0,
            step_beats=1.0,
            duration_beats=1.34,
            velocity_pattern=(0.66, 0.54, 0.61, 0.50),
            pan_pattern=(-0.52, 0.46, -0.24, 0.56),
            repeats=repeats,
        ),
        config.total_beats,
    )
    plucks = _bounded(
        events_from_steps(
            (0, 7, None, 12, 10, None, 7, 3),
            root_note=45.0,
            step_beats=0.5,
            duration_beats=0.70,
            velocity_pattern=(0.82, 0.58, 0.68, 0.76, 0.64, 0.56, 0.72, 0.61),
            pan_pattern=(0.36, -0.42, 0.24, -0.30),
            repeats=repeats,
        ),
        config.total_beats,
    )

    tracks = {
        "fm": TrackSpec("phase-machine bass", "fm", bass, 0.82, 0x11),
        "additive": TrackSpec("harmonic glass", "additive", glass, 0.54, 0x22),
        "karplus": TrackSpec("deterministic wire", "karplus", plucks, 0.63, 0x33),
    }
    if config.voice_mode == "hybrid":
        return tracks["fm"], tracks["additive"], tracks["karplus"]
    return (tracks[config.voice_mode],)
