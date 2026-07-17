"""Numerical constants shared by the mathematical source layer.

The constants are evaluated once with Python's binary64 ``float`` semantics.
Keeping them in one module prevents subtly different spellings or precisions
from entering replay-safe render paths.
"""

from __future__ import annotations

import math
from typing import Final

PHI: Final[float] = (1.0 + math.sqrt(5.0)) / 2.0
"""The golden ratio, ``(1 + sqrt(5)) / 2``."""

TAU: Final[float] = math.tau
"""One full angular turn, ``2 * pi``, in radians."""

HALF_PI: Final[float] = math.pi / 2.0
"""A quadrature phase offset, ``pi / 2``, in radians."""
