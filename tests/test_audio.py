"""PCM quantization and canonical RIFF/WAVE packing tests."""

from __future__ import annotations

import struct

import numpy as np
import pytest

from sonification.core.audio import pcm_payload_bytes, quantize_pcm, wav_bytes_from_pcm


@pytest.mark.parametrize("bit_depth", [16, 24])
def test_quantization_is_symmetric_half_away_from_zero(bit_depth: int) -> None:
    limit = (1 << (bit_depth - 1)) - 1
    audio = np.asarray(
        [
            -2.0,
            -1.0,
            -1.5 / limit,
            -0.5 / limit,
            0.0,
            0.5 / limit,
            1.5 / limit,
            1.0,
            2.0,
        ],
        dtype=np.float64,
    )

    actual = quantize_pcm(audio, bit_depth).ravel()
    expected = np.asarray([-limit, -limit, -2, -1, 0, 1, 2, limit, limit], dtype=np.int32)
    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("bit_depth", [16, 24])
def test_pcm_payload_is_signed_little_endian_and_interleaved(bit_depth: int) -> None:
    limit = (1 << (bit_depth - 1)) - 1
    bytes_per_sample = bit_depth // 8
    pcm = np.asarray(
        [[-limit, -2], [-1, 0], [1, 2], [limit, 17]],
        dtype=np.int32,
    )

    payload = pcm_payload_bytes(pcm, bit_depth)
    expected = b"".join(
        int(value).to_bytes(bytes_per_sample, byteorder="little", signed=True)
        for value in pcm.ravel(order="C")
    )

    assert payload == expected


@pytest.mark.parametrize("bit_depth", [16, 24])
def test_wav_header_and_payload_lengths_are_canonical(bit_depth: int) -> None:
    sample_rate = 8_000
    pcm = np.asarray([[-3, 4], [5, -6], [7, 8]], dtype=np.int32)

    wav, payload = wav_bytes_from_pcm(pcm, sample_rate, bit_depth)
    header = struct.unpack("<4sI4s4sIHHIIHH4sI", wav[:44])
    bytes_per_sample = bit_depth // 8
    expected_payload_size = pcm.shape[0] * pcm.shape[1] * bytes_per_sample

    assert header == (
        b"RIFF",
        36 + expected_payload_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        2,
        sample_rate,
        sample_rate * 2 * bytes_per_sample,
        2 * bytes_per_sample,
        bit_depth,
        b"data",
        expected_payload_size,
    )
    assert len(wav) == 44 + expected_payload_size
    assert wav[44:] == payload
    assert payload == pcm_payload_bytes(pcm, bit_depth)


def test_pcm_validation_happens_before_narrowing_or_truncation() -> None:
    with pytest.raises(ValueError, match="outside"):
        pcm_payload_bytes(np.asarray([[1 << 32]], dtype=np.int64), 16)
    with pytest.raises(TypeError, match="integer"):
        pcm_payload_bytes(np.asarray([[1.9]], dtype=np.float64), 16)


def test_odd_sized_mono_pcm24_data_chunk_has_riff_pad_byte() -> None:
    pcm = np.asarray([[1], [2], [3]], dtype=np.int32)
    wav, payload = wav_bytes_from_pcm(pcm, 8_000, 24)
    header = struct.unpack("<4sI4s4sIHHIIHH4sI", wav[:44])

    assert len(payload) == 9
    assert header[1] == 36 + 9 + 1
    assert header[-1] == 9
    assert wav[44:53] == payload
    assert wav[-1:] == b"\0"
