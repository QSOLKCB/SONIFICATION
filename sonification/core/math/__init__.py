"""Deterministic mathematical building blocks for procedural sonification."""

from .base import FloatArray, MathSource, validate_render_request
from .constants import HALF_PI, PHI, TAU
from .prng import (
    GOLDEN_GAMMA,
    UINT64_MASK,
    SplitMix64,
    splitmix64,
    splitmix64_array,
    splitmix64_at_indices,
    uint64_array_to_float64,
    uint64_to_float64,
    validate_uint64,
)
from .sources import (
    ConstantSource,
    DeterministicNoiseSource,
    FractalNoiseSource,
    LogisticSource,
    SineSource,
)

__all__ = [
    "GOLDEN_GAMMA",
    "HALF_PI",
    "PHI",
    "TAU",
    "UINT64_MASK",
    "ConstantSource",
    "DeterministicNoiseSource",
    "FloatArray",
    "FractalNoiseSource",
    "LogisticSource",
    "MathSource",
    "SineSource",
    "SplitMix64",
    "splitmix64",
    "splitmix64_array",
    "splitmix64_at_indices",
    "uint64_array_to_float64",
    "uint64_to_float64",
    "validate_render_request",
    "validate_uint64",
]
