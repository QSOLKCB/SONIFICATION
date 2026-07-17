"""Extensible rhythm generator contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from .events import NoteEvent


class RhythmGenerator(ABC):
    """Abstract deterministic event generator for future rhythm systems."""

    @abstractmethod
    def generate(self, *, total_beats: int, seed: int) -> Sequence[NoteEvent]:
        """Return events inside ``[0, total_beats)`` in deterministic order."""
