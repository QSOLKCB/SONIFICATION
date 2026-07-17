"""Deterministic PCM quantization and minimal RIFF/WAVE packing."""

from __future__ import annotations

import math
import struct
from numbers import Integral

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int32]


def _validate_bit_depth(bit_depth: int) -> int:
    if isinstance(bit_depth, bool) or not isinstance(bit_depth, Integral):
        raise TypeError("bit_depth must be an integer")
    normalized = int(bit_depth)
    if normalized not in (16, 24):
        raise ValueError("bit_depth must be 16 or 24")
    return normalized


def _validate_sample_rate(sample_rate: int) -> int:
    if isinstance(sample_rate, bool) or not isinstance(sample_rate, Integral):
        raise TypeError("sample_rate must be an integer")
    normalized = int(sample_rate)
    if not 8_000 <= normalized <= 192_000:
        raise ValueError("sample_rate must be between 8000 and 192000")
    return normalized


def _validate_pcm(pcm: NDArray[np.integer], bit_depth: int) -> IntArray:
    depth = _validate_bit_depth(bit_depth)
    values = np.asarray(pcm)
    if values.dtype.kind not in {"i", "u"}:
        raise TypeError("pcm must contain integer samples")
    if values.ndim == 1:
        values = values[:, np.newaxis]
    if values.ndim != 2 or values.shape[0] < 1 or values.shape[1] not in (1, 2):
        raise ValueError("pcm must contain at least one frame and one or two channels")
    limit = (1 << (depth - 1)) - 1
    if np.any(values > limit):
        raise ValueError("pcm value is outside the selected bit-depth range")
    if values.dtype.kind == "i" and np.any(values < -limit):
        raise ValueError("pcm value is outside the selected bit-depth range")
    return np.ascontiguousarray(values, dtype=np.int32)


def validate_audio(audio: NDArray[np.floating]) -> FloatArray:
    """Return contiguous finite float64 audio with shape ``(frames, channels)``."""

    array = np.asarray(audio, dtype=np.float64)
    if array.ndim == 1:
        array = array[:, np.newaxis]
    if array.ndim != 2 or array.shape[0] < 1 or array.shape[1] not in (1, 2):
        raise ValueError("audio must have shape (frames,), (frames, 1), or (frames, 2)")
    if not np.all(np.isfinite(array)):
        raise ValueError("audio contains non-finite samples")
    return np.ascontiguousarray(array)


def normalize_peak(audio: NDArray[np.floating], target_dbfs: float = -3.0) -> FloatArray:
    """Peak-normalize a copy of audio to an explicit dBFS target."""

    if not math.isfinite(target_dbfs) or not -96.0 <= target_dbfs <= 0.0:
        raise ValueError("target_dbfs must be finite and between -96 and 0")
    array = validate_audio(audio).copy()
    peak = float(np.max(np.abs(array)))
    if peak == 0.0:
        return array
    target = 10.0 ** (target_dbfs / 20.0)
    array *= target / peak
    return array


def rational_soft_clip(audio: NDArray[np.floating], drive: float = 1.15) -> FloatArray:
    """Apply a bounded algebraic soft clip without a platform libm call."""

    if not math.isfinite(drive) or not 0.01 <= drive <= 16.0:
        raise ValueError("drive must be finite and between 0.01 and 16")
    array = validate_audio(audio)
    driven = array * drive
    return np.ascontiguousarray(driven / (1.0 + np.abs(driven)), dtype=np.float64)


def quantize_pcm(audio: NDArray[np.floating], bit_depth: int) -> IntArray:
    """Quantize with explicit symmetric half-away-from-zero rounding."""

    bit_depth = _validate_bit_depth(bit_depth)
    array = np.clip(validate_audio(audio), -1.0, 1.0)
    positive_limit = float((1 << (bit_depth - 1)) - 1)
    scaled = array * positive_limit
    rounded = np.where(scaled >= 0.0, np.floor(scaled + 0.5), np.ceil(scaled - 0.5))
    return np.ascontiguousarray(rounded, dtype=np.int32)


def pcm_payload_bytes(pcm: NDArray[np.integer], bit_depth: int) -> bytes:
    """Pack interleaved signed PCM into deterministic little-endian bytes."""

    bit_depth = _validate_bit_depth(bit_depth)
    values = _validate_pcm(pcm, bit_depth)
    flat = np.ascontiguousarray(values).reshape(-1)
    if bit_depth == 16:
        return flat.astype("<i2", copy=False).tobytes(order="C")

    unsigned = np.bitwise_and(flat.astype(np.int64), 0xFFFFFF)
    packed = np.empty((flat.size, 3), dtype=np.uint8)
    packed[:, 0] = unsigned & 0xFF
    packed[:, 1] = (unsigned >> 8) & 0xFF
    packed[:, 2] = (unsigned >> 16) & 0xFF
    return packed.tobytes(order="C")


def wav_bytes_from_pcm(
    pcm: NDArray[np.integer], sample_rate: int, bit_depth: int
) -> tuple[bytes, bytes]:
    """Return canonical RIFF/WAVE bytes and the identity-bearing PCM payload."""

    sample_rate = _validate_sample_rate(sample_rate)
    bit_depth = _validate_bit_depth(bit_depth)
    values = _validate_pcm(pcm, bit_depth)
    payload = pcm_payload_bytes(values, bit_depth)
    padding = b"\0" if len(payload) & 1 else b""
    channels = int(values.shape[1])
    block_align = channels * (bit_depth // 8)
    byte_rate = sample_rate * block_align
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(payload) + len(padding),
        b"WAVE",
        b"fmt ",
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bit_depth,
        b"data",
        len(payload),
    )
    return header + payload + padding, payload


def encode_wav(
    audio: NDArray[np.floating], sample_rate: int, bit_depth: int
) -> tuple[bytes, bytes, IntArray]:
    """Quantize float audio and return ``(wav_bytes, pcm_bytes, pcm_array)``."""

    pcm = quantize_pcm(audio, bit_depth)
    wav, payload = wav_bytes_from_pcm(pcm, sample_rate, bit_depth)
    return wav, payload, pcm
