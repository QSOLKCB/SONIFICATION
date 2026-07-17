"""Render the Phase 1 factory loop without invoking the CLI parser."""

from pathlib import Path

from sonification.config import LoopConfig
from sonification.core.provenance import canonical_json_bytes
from sonification.renderer import render_loop


def main() -> None:
    config = LoopConfig(bars=4, tempo_bpm=128.0, seed=2026, voice_mode="hybrid")
    result = render_loop(config)
    output = Path("artifacts")
    output.mkdir(exist_ok=True)
    stem = f"phase1_example_{result.wav_sha256[:12]}"
    (output / f"{stem}.wav").write_bytes(result.wav_bytes)
    (output / f"{stem}.manifest.json").write_bytes(canonical_json_bytes(result.manifest))
    print(result.wav_sha256)


if __name__ == "__main__":
    main()
