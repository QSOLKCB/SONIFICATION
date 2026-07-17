"""Canonical serialization and acyclic provenance integrity tests."""

from __future__ import annotations

import hashlib
from copy import deepcopy

import numpy as np
import pytest

from sonification.core.audio import encode_wav
from sonification.core.provenance import (
    CONTRACT_DOMAIN,
    FINGERPRINT_DOMAIN,
    MANIFEST_CORE_DOMAIN,
    RECIPE_DOMAIN,
    build_fingerprint,
    build_manifest,
    canonical_json_bytes,
    domain_hash,
    validate_manifest_integrity,
)


def _fingerprint() -> dict[str, object]:
    audio = np.asarray(
        [[-0.75, 0.25], [-0.25, 0.75], [0.0, 0.0], [0.5, -0.5]],
        dtype=np.float64,
    )
    wav, pcm_bytes, pcm = encode_wav(audio, sample_rate=8_000, bit_depth=16)
    return build_fingerprint(
        pcm,
        pcm_bytes=pcm_bytes,
        wav_bytes=wav,
        sample_rate=8_000,
        bit_depth=16,
        envelope_bins=2,
        chunk_count=2,
    )


def test_canonical_json_is_sorted_utf8_compact_and_newline_terminated() -> None:
    value = {"z": 1, "a": "café", "nested": {"b": True, "a": None}}

    assert canonical_json_bytes(value) == (
        b'{"a":"caf\xc3\xa9","nested":{"a":null,"b":true},"z":1}\n'
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), (1, 2)])
def test_canonical_json_rejects_non_json_or_non_finite_values(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        canonical_json_bytes({"value": value})


def test_domain_hash_binds_domain_and_canonical_content() -> None:
    value = {"b": 2, "a": 1}
    expected = hashlib.sha256(RECIPE_DOMAIN + canonical_json_bytes(value)).hexdigest()

    assert domain_hash(RECIPE_DOMAIN, value) == expected
    assert domain_hash(RECIPE_DOMAIN, {"a": 1, "b": 2}) == expected
    assert domain_hash(RECIPE_DOMAIN, {"a": 1, "b": 3}) != expected
    with pytest.raises(ValueError, match="NUL"):
        domain_hash(b"domain-without-terminator", value)


def test_manifest_integrity_chain_is_acyclic_and_recomputable() -> None:
    recipe = {"schema": "test.recipe/v1", "render": {"seed": "0x0000000000000001"}}
    fingerprint = _fingerprint()
    manifest = build_manifest(
        application_version="test",
        recipe=recipe,
        fingerprint=fingerprint,
        source_lineage=[{"relationship": "test", "source": "unit"}],
    )

    assert manifest["recipe_sha256"] == domain_hash(RECIPE_DOMAIN, recipe)

    fingerprint_core = dict(manifest["fingerprint"])
    fingerprint_sha = fingerprint_core.pop("fingerprint_sha256")
    assert fingerprint_sha == domain_hash(FINGERPRINT_DOMAIN, fingerprint_core)

    contract_core = dict(manifest["contract"])
    contract_sha = contract_core.pop("contract_sha256")
    assert contract_sha == domain_hash(CONTRACT_DOMAIN, contract_core)

    manifest_core = dict(manifest)
    manifest_sha = manifest_core.pop("manifest_core_sha256")
    assert "manifest_core_sha256" not in manifest_core
    assert manifest_sha == domain_hash(MANIFEST_CORE_DOMAIN, manifest_core)
    validate_manifest_integrity(manifest)


def test_fingerprint_and_manifest_tampering_break_integrity() -> None:
    recipe = {"schema": "test.recipe/v1", "value": 1}
    fingerprint = _fingerprint()
    tampered_fingerprint = deepcopy(fingerprint)
    tampered_fingerprint["frames"] = int(tampered_fingerprint["frames"]) + 1

    with pytest.raises(ValueError, match="fingerprint integrity check failed"):
        build_manifest(
            application_version="test",
            recipe=recipe,
            fingerprint=tampered_fingerprint,
        )

    manifest = build_manifest(
        application_version="test",
        recipe=recipe,
        fingerprint=fingerprint,
    )
    tampered_manifest = deepcopy(manifest)
    tampered_manifest["claim_boundary"] += " tampered"
    recorded_hash = tampered_manifest.pop("manifest_core_sha256")
    assert domain_hash(MANIFEST_CORE_DOMAIN, tampered_manifest) != recorded_hash


def test_fingerprint_rejects_unrelated_pcm_or_wav_bytes() -> None:
    audio = np.zeros((4, 2), dtype=np.float64)
    wav, pcm_bytes, pcm = encode_wav(audio, 8_000, 16)

    with pytest.raises(ValueError, match="pcm_bytes"):
        build_fingerprint(
            pcm,
            pcm_bytes=pcm_bytes + b"\0",
            wav_bytes=wav,
            sample_rate=8_000,
            bit_depth=16,
        )
    with pytest.raises(ValueError, match="wav_bytes"):
        build_fingerprint(
            pcm,
            pcm_bytes=pcm_bytes,
            wav_bytes=wav + b"\0",
            sample_rate=8_000,
            bit_depth=16,
        )


@pytest.mark.parametrize("frame_count", [1, 4])
def test_fingerprint_clamps_envelope_bins_to_pcm_frames(frame_count: int) -> None:
    audio = np.linspace(-0.5, 0.5, frame_count, dtype=np.float64)[:, np.newaxis]
    wav, pcm_bytes, pcm = encode_wav(audio, 8_000, 16)

    fingerprint = build_fingerprint(
        pcm,
        pcm_bytes=pcm_bytes,
        wav_bytes=wav,
        sample_rate=8_000,
        bit_depth=16,
        envelope_bins=32,
    )

    envelope = fingerprint["rms_envelope_ppm"]
    assert len(envelope) == frame_count
    assert all(isinstance(value, int) and value >= 0 for value in envelope)
