"""Sample-free deterministic synthesis engines.

All public instruments return one-dimensional, finite ``numpy.float64`` arrays.
The requested duration is the gate length; each instrument appends its configured
release tail.
"""

from .additive import AdditiveSynth
from .base import INSTRUMENT_ABI, IdentityDict, Instrument, MonoSignal
from .envelopes import ADSREnvelope, PluckEnvelope
from .fm import FMSynth
from .karplus_strong import KarplusStrong, KarplusStrongSynth
from .oscillators import (
    band_limited_saw,
    band_limited_square,
    decimate_fir,
    deterministic_excitation,
    deterministic_phase,
    deterministic_unit,
    sine_oscillator,
)

__all__ = [
    "INSTRUMENT_ABI",
    "ADSREnvelope",
    "AdditiveSynth",
    "FMSynth",
    "IdentityDict",
    "Instrument",
    "KarplusStrong",
    "KarplusStrongSynth",
    "MonoSignal",
    "PluckEnvelope",
    "band_limited_saw",
    "band_limited_square",
    "decimate_fir",
    "deterministic_excitation",
    "deterministic_phase",
    "deterministic_unit",
    "sine_oscillator",
]
