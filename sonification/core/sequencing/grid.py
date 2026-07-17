"""Small explicit step-grid adapter used by the Phase 1 composition."""

from __future__ import annotations

from collections.abc import Sequence
from numbers import Integral, Real

from .events import NoteEvent


def events_from_steps(
    steps: Sequence[int | None],
    *,
    root_note: float,
    step_beats: float,
    duration_beats: float,
    velocity_pattern: Sequence[float] = (0.84, 0.68, 0.76, 0.64),
    pan_pattern: Sequence[float] = (0.0,),
    repeats: int = 1,
) -> tuple[NoteEvent, ...]:
    """Convert semitone offsets into a stable, ordered note-event tuple.

    ``None`` represents a rest. This intentionally modest Phase 1 adapter is
    replaced or driven by Phi, Fibonacci, Euclidean, CA, and attractor rhythm
    generators in later phases without changing the event contract.
    """

    if not steps:
        raise ValueError("steps must not be empty")
    if isinstance(repeats, bool) or not isinstance(repeats, Integral):
        raise TypeError("repeats must be an integer")
    repeats = int(repeats)
    if step_beats <= 0.0 or duration_beats <= 0.0:
        raise ValueError("step_beats and duration_beats must be positive")
    if not velocity_pattern or not pan_pattern:
        raise ValueError("velocity_pattern and pan_pattern must not be empty")
    if repeats < 1:
        raise ValueError("repeats must be positive")

    events: list[NoteEvent] = []
    pattern_beats = len(steps) * step_beats
    for repeat in range(repeats):
        for index, offset in enumerate(steps):
            if offset is None:
                continue
            if isinstance(offset, bool) or not isinstance(offset, Integral):
                raise TypeError("step offsets must be integers or None")
            velocity = velocity_pattern[index % len(velocity_pattern)]
            pan = pan_pattern[index % len(pan_pattern)]
            if isinstance(velocity, bool) or not isinstance(velocity, Real):
                raise TypeError("velocity values must be real numbers")
            if isinstance(pan, bool) or not isinstance(pan, Real):
                raise TypeError("pan values must be real numbers")
            events.append(
                NoteEvent(
                    onset_beats=repeat * pattern_beats + index * step_beats,
                    duration_beats=duration_beats,
                    note=root_note + offset,
                    velocity=float(velocity),
                    pan=float(pan),
                )
            )
    return tuple(events)
