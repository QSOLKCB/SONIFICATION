"""Canonical hashes, signal fingerprints, and acyclic provenance manifests."""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from itertools import pairwise
from pathlib import Path
from typing import Any, Final

import numpy as np
from numpy.typing import NDArray

from .audio import wav_bytes_from_pcm

RECIPE_DOMAIN: Final = b"SONIFICATION/RECIPE/v1\0"
FINGERPRINT_DOMAIN: Final = b"SONIFICATION/FINGERPRINT/v1\0"
CONTRACT_DOMAIN: Final = b"SONIFICATION/CONTRACT/v1\0"
MANIFEST_CORE_DOMAIN: Final = b"SONIFICATION/MANIFEST-CORE/v1\0"


def _assert_json_value(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (bool, str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite float at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"non-string object key at {path}")
            _assert_json_value(item, f"{path}.{key}")
        return
    raise TypeError(f"unsupported canonical JSON value at {path}: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize supported JSON values with sorted keys and one final newline."""

    _assert_json_value(value)
    text = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (text + "\n").encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Return ordinary SHA-256 for exact file or payload identity."""

    return hashlib.sha256(data).hexdigest()


def domain_hash(domain: bytes, value: Any) -> str:
    """Hash canonical JSON under a versioned, NUL-terminated domain."""

    if not domain.endswith(b"\0"):
        raise ValueError("hash domains must end with NUL")
    return sha256_hex(domain + canonical_json_bytes(value))


def _round_float(value: float, digits: int = 12) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == 0.0 else rounded


def build_fingerprint(
    pcm: NDArray[np.integer],
    *,
    pcm_bytes: bytes,
    wav_bytes: bytes,
    sample_rate: int,
    bit_depth: int,
    envelope_bins: int = 32,
    chunk_count: int = 16,
) -> dict[str, Any]:
    """Build deterministic exact hashes plus bounded PCM observations."""

    if isinstance(sample_rate, bool) or not isinstance(sample_rate, int):
        raise TypeError("sample_rate must be an integer")
    if not 8_000 <= sample_rate <= 192_000:
        raise ValueError("sample_rate must be between 8000 and 192000")
    if isinstance(bit_depth, bool) or not isinstance(bit_depth, int):
        raise TypeError("bit_depth must be an integer")
    if bit_depth not in (16, 24):
        raise ValueError("bit_depth must be 16 or 24")
    expected_wav, expected_pcm_bytes = wav_bytes_from_pcm(pcm, sample_rate, bit_depth)
    if pcm_bytes != expected_pcm_bytes:
        raise ValueError("pcm_bytes do not match pcm samples")
    if wav_bytes != expected_wav:
        raise ValueError("wav_bytes do not match pcm samples and format")

    values = np.asarray(pcm, dtype=np.int64)
    if values.ndim == 1:
        values = values[:, np.newaxis]
    if values.ndim != 2 or values.shape[0] < 1 or values.shape[1] not in (1, 2):
        raise ValueError("pcm must contain at least one mono or stereo frame")
    if envelope_bins < 1 or chunk_count < 1:
        raise ValueError("envelope_bins and chunk_count must be positive")

    full_scale = float((1 << (bit_depth - 1)) - 1)
    normalized = values.astype(np.float64) / full_scale
    peak = float(np.max(np.abs(normalized)))
    rms = float(np.sqrt(np.mean(normalized * normalized)))
    dc = np.mean(normalized, axis=0)
    crossings = int(np.count_nonzero((values[1:] >= 0) != (values[:-1] >= 0)))
    clipping = int(np.count_nonzero(np.abs(values) >= int(full_scale)))

    if values.shape[1] == 2:
        left = normalized[:, 0] - float(np.mean(normalized[:, 0]))
        right = normalized[:, 1] - float(np.mean(normalized[:, 1]))
        denominator = float(np.sqrt(np.dot(left, left) * np.dot(right, right)))
        correlation = float(np.dot(left, right) / denominator) if denominator > 0.0 else 0.0
    else:
        correlation = 1.0

    frame_splits = np.linspace(0, values.shape[0], envelope_bins + 1, dtype=np.int64)
    envelope_ppm: list[int] = []
    for start, stop in pairwise(frame_splits):
        segment = normalized[int(start) : max(int(start) + 1, int(stop))]
        segment_rms = float(np.sqrt(np.mean(segment * segment)))
        envelope_ppm.append(round(segment_rms * 1_000_000.0))

    byte_splits = np.linspace(0, len(pcm_bytes), chunk_count + 1, dtype=np.int64)
    chunk_hashes = [
        sha256_hex(pcm_bytes[int(start) : int(stop)]) for start, stop in pairwise(byte_splits)
    ]
    core: dict[str, Any] = {
        "schema": "sonification.audio-fingerprint/v1",
        "sample_rate": sample_rate,
        "bit_depth": bit_depth,
        "frames": int(values.shape[0]),
        "channels": int(values.shape[1]),
        "pcm_sha256": sha256_hex(pcm_bytes),
        "wav_sha256": sha256_hex(wav_bytes),
        "peak": _round_float(peak),
        "rms": _round_float(rms),
        "dc_offset": [_round_float(item) for item in dc],
        "crest_factor": _round_float(peak / rms) if rms > 0.0 else 0.0,
        "zero_crossings": crossings,
        "stereo_correlation": _round_float(correlation),
        "clipping_sample_count": clipping,
        "rms_envelope_ppm": envelope_ppm,
        "rms_envelope_sha256": domain_hash(b"SONIFICATION/RMS-ENVELOPE/v1\0", envelope_ppm),
        "pcm_chunk_sha256": chunk_hashes,
    }
    return {**core, "fingerprint_sha256": domain_hash(FINGERPRINT_DOMAIN, core)}


def build_manifest(
    *,
    application_version: str,
    recipe: dict[str, Any],
    fingerprint: dict[str, Any],
    source_lineage: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Bind recipe and audio without circular self-hashing or timestamps."""

    recipe_copy = deepcopy(recipe)
    fingerprint_copy = deepcopy(fingerprint)
    recipe_sha = domain_hash(RECIPE_DOMAIN, recipe_copy)
    fingerprint_core = dict(fingerprint_copy)
    recorded_fingerprint_sha = fingerprint_core.pop("fingerprint_sha256", None)
    calculated_fingerprint_sha = domain_hash(FINGERPRINT_DOMAIN, fingerprint_core)
    if recorded_fingerprint_sha != calculated_fingerprint_sha:
        raise ValueError("fingerprint integrity check failed")

    contract_core: dict[str, Any] = {
        "schema": "sonification.render-contract/v1",
        "recipe_sha256": recipe_sha,
        "fingerprint_sha256": calculated_fingerprint_sha,
        "pcm_sha256": fingerprint_copy["pcm_sha256"],
        "wav_sha256": fingerprint_copy["wav_sha256"],
        "sample_format": f"pcm_s{fingerprint_copy['bit_depth']}le",
        "determinism_scope": (
            "same-version-same-runtime-bit-identical; cross-runtime-float64-tolerance"
        ),
    }
    contract_sha = domain_hash(CONTRACT_DOMAIN, contract_core)
    manifest_core: dict[str, Any] = {
        "schema": "sonification.manifest/v1",
        "application": {"name": "QSOL SONIFICATION", "version": application_version},
        "phase": 1,
        "recipe": recipe_copy,
        "recipe_sha256": recipe_sha,
        "fingerprint": fingerprint_copy,
        "contract": {**contract_core, "contract_sha256": contract_sha},
        "lineage": deepcopy(source_lineage or []),
        "claim_boundary": (
            "This artifact is mathematical composition and audible geometry. "
            "It is not evidence that E8 or another sonified structure is "
            "physically present in nature."
        ),
    }
    return {
        **manifest_core,
        "manifest_core_sha256": domain_hash(MANIFEST_CORE_DOMAIN, manifest_core),
    }


def validate_manifest_integrity(manifest: dict[str, Any]) -> None:
    """Validate the complete unkeyed manifest hash chain.

    This proves internal consistency and detects unrecomputed changes. SHA-256
    is not a signature or a claim about who created the document.
    """

    if not isinstance(manifest, dict):
        raise TypeError("manifest root must be a JSON object")
    manifest_core = dict(manifest)
    manifest_sha = manifest_core.pop("manifest_core_sha256", None)
    if (
        not isinstance(manifest_sha, str)
        or domain_hash(MANIFEST_CORE_DOMAIN, manifest_core) != manifest_sha
    ):
        raise ValueError("manifest core integrity check failed")

    recipe = manifest.get("recipe")
    if not isinstance(recipe, dict):
        raise TypeError("manifest recipe must be a JSON object")
    recipe_sha = manifest.get("recipe_sha256")
    if not isinstance(recipe_sha, str) or domain_hash(RECIPE_DOMAIN, recipe) != recipe_sha:
        raise ValueError("recipe integrity check failed")

    fingerprint = manifest.get("fingerprint")
    if not isinstance(fingerprint, dict):
        raise TypeError("manifest fingerprint must be a JSON object")
    fingerprint_core = dict(fingerprint)
    fingerprint_sha = fingerprint_core.pop("fingerprint_sha256", None)
    if (
        not isinstance(fingerprint_sha, str)
        or domain_hash(FINGERPRINT_DOMAIN, fingerprint_core) != fingerprint_sha
    ):
        raise ValueError("fingerprint integrity check failed")

    contract = manifest.get("contract")
    if not isinstance(contract, dict):
        raise TypeError("manifest contract must be a JSON object")
    contract_core = dict(contract)
    contract_sha = contract_core.pop("contract_sha256", None)
    if (
        not isinstance(contract_sha, str)
        or domain_hash(CONTRACT_DOMAIN, contract_core) != contract_sha
    ):
        raise ValueError("render contract integrity check failed")
    if contract_core.get("recipe_sha256") != recipe_sha:
        raise ValueError("render contract recipe link differs")
    if contract_core.get("fingerprint_sha256") != fingerprint_sha:
        raise ValueError("render contract fingerprint link differs")
    if contract_core.get("pcm_sha256") != fingerprint.get("pcm_sha256"):
        raise ValueError("render contract PCM link differs")
    if contract_core.get("wav_sha256") != fingerprint.get("wav_sha256"):
        raise ValueError("render contract WAV link differs")


def write_canonical_json(path: Path, value: Any) -> None:
    """Write canonical JSON bytes to a local artifact path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))
