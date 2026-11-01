"""Security regression controls for local SONIFICATION manifest verification."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import sonification.cli as cli
from sonification.config import LoopConfig


def test_verifier_rejects_accepted_large_render_before_synthesis(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Valid for normal generation (exactly ten million frames), but must
    # not be accepted for replay of an untrusted incoming manifest.
    config = LoopConfig(
        tempo_bpm=384.0, bars=64, beats_per_bar=16,
        sample_rate=62_500, bit_depth=24, voice_mode="hybrid"
    )
    assert config.frame_count == 10_000_000
    with pytest.raises(ValueError, match="verifier resource budget"):
        cli._verify_budget(config)

    document = {
        "schema": "sonification.manifest/v1",
        "recipe": {"render": {"config": config.to_identity_dict()}},
        "fingerprint": {"wav_sha256": "0" * 64},
    }
    supplied = tmp_path / "heavy.json"
    supplied.write_text(json.dumps(document), encoding="utf-8")
    # The test isolates the resource preflight; it does not claim that this
    # synthetic manifest has a valid signed or hash-chain identity.
    monkeypatch.setattr(cli, "validate_manifest_integrity", lambda _: None)

    def forbid_render(_: LoopConfig) -> None:
        raise AssertionError("verifier called renderer before its budget check")

    monkeypatch.setattr(cli, "render_loop", forbid_render)
    passed, message = cli._verify(supplied)
    assert not passed
    assert "verifier resource budget" in message


def test_default_render_fits_verifier_budget() -> None:
    cli._verify_budget(LoopConfig())


def test_oversized_sparse_manifest_is_rejected_before_read(tmp_path: Path) -> None:
    supplied = tmp_path / "oversized.json"
    with supplied.open("wb") as handle:
        handle.truncate(cli._MAX_MANIFEST_BYTES + 1)
    passed, message = cli._verify(supplied)
    assert not passed
    assert "manifest exceeds" in message


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="requires POSIX FIFO support")
def test_fifo_manifest_is_rejected_without_blocking(tmp_path: Path) -> None:
    fifo = tmp_path / "incoming.fifo"
    os.mkfifo(fifo)
    passed, message = cli._verify(fifo)
    assert not passed
    assert "regular file" in message


def test_symlink_manifest_is_not_followed(tmp_path: Path) -> None:
    real = tmp_path / "real.json"
    real.write_text("{}", encoding="utf-8")
    symbolic = tmp_path / "link.json"
    symbolic.symlink_to(real)
    passed, message = cli._verify(symbolic)
    assert not passed
    assert "PASS" not in message
