"""Headless command-line interface for deterministic loop generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import __version__
from .config import LoopConfig
from .core.provenance import canonical_json_bytes, validate_manifest_integrity
from .renderer import RenderResult, render_loop

_EXPORTS = frozenset({"wav", "manifest", "recipe", "fingerprint"})
_MAX_MANIFEST_BYTES = 16 * 1024 * 1024
LOGGER = logging.getLogger(__name__)


def _exports(value: str) -> frozenset[str]:
    items = {item.strip().lower() for item in value.split(",") if item.strip()}
    if items == {"all"}:
        return _EXPORTS
    unknown = items - _EXPORTS
    if not items or unknown:
        detail = ", ".join(sorted(unknown)) if unknown else "empty selection"
        raise argparse.ArgumentTypeError(f"invalid export selection: {detail}")
    return frozenset(items)


def _safe_name(value: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
    if not name:
        raise argparse.ArgumentTypeError("name must contain a letter or number")
    return name[:96]


def _write_result(
    result: RenderResult,
    *,
    output_dir: Path,
    name: str | None,
    exports: frozenset[str],
    force: bool = False,
) -> dict[str, Path]:
    validate_manifest_integrity(result.manifest)
    if result.recipe != result.manifest.get("recipe"):
        raise ValueError("result recipe differs from its manifest-bound recipe")
    if result.fingerprint != result.manifest.get("fingerprint"):
        raise ValueError("result fingerprint differs from its manifest-bound fingerprint")
    manifest_fingerprint = result.manifest["fingerprint"]
    if hashlib.sha256(result.wav_bytes).hexdigest() != manifest_fingerprint["wav_sha256"]:
        raise ValueError("result WAV bytes differ from the manifest fingerprint")
    if hashlib.sha256(result.pcm_bytes).hexdigest() != manifest_fingerprint["pcm_sha256"]:
        raise ValueError("result PCM bytes differ from the manifest fingerprint")

    output_dir.mkdir(parents=True, exist_ok=True)
    base = name or f"sonification_{result.config.voice_mode}_{result.wav_sha256[:12]}"
    artifacts: dict[str, tuple[str, bytes]] = {
        "wav": ("wav", result.wav_bytes),
        "manifest": ("manifest.json", canonical_json_bytes(result.manifest)),
        "recipe": ("recipe.json", canonical_json_bytes(result.manifest["recipe"])),
        "fingerprint": (
            "fingerprint.json",
            canonical_json_bytes(manifest_fingerprint),
        ),
    }
    destinations: dict[str, Path] = {}
    for kind in sorted(exports):
        suffix, _ = artifacts[kind]
        path = output_dir / f"{base}.{suffix}"
        if path.exists() and not force:
            raise FileExistsError(f"artifact exists; use --force to replace it: {path}")
        destinations[kind] = path

    staged: dict[str, Path] = {}
    try:
        for kind in destinations:
            payload = artifacts[kind][1]
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".sonification-", dir=output_dir, delete=False
            ) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
                staged[kind] = Path(handle.name)
        for kind, destination in destinations.items():
            os.replace(staged.pop(kind), destination)
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
    return destinations


def _config_from_recipe(recipe: dict[str, Any]) -> LoopConfig:
    config = recipe.get("render", {}).get("config", {})
    if not isinstance(config, dict):
        raise ValueError("manifest recipe does not contain a render config")
    fields = {
        "tempo_bpm",
        "bars",
        "beats_per_bar",
        "sample_rate",
        "bit_depth",
        "tuning_a4_hz",
        "seed",
        "peak_dbfs",
        "voice_mode",
    }
    if not fields.issubset(config):
        missing = ", ".join(sorted(fields - set(config)))
        raise ValueError(f"manifest render config is missing: {missing}")
    values = {field: config[field] for field in fields}
    seed = values["seed"]
    if not isinstance(seed, str) or not re.fullmatch(r"0x[0-9a-f]{16}", seed):
        raise ValueError("manifest seed must be canonical uint64 hexadecimal")
    values["seed"] = int(seed, 16)
    return LoopConfig(**values)


def _verify(path: Path) -> tuple[bool, str]:
    try:
        if path.stat().st_size > _MAX_MANIFEST_BYTES:
            return False, f"manifest exceeds {_MAX_MANIFEST_BYTES} byte limit"
        manifest = json.loads(path.read_bytes().decode("utf-8"))
        if not isinstance(manifest, dict):
            return False, "manifest root must be a JSON object"
        if manifest.get("schema") != "sonification.manifest/v1":
            return False, "unsupported manifest schema"
        validate_manifest_integrity(manifest)
        recipe = manifest.get("recipe")
        if not isinstance(recipe, dict):
            return False, "manifest recipe is missing"
        result = render_loop(_config_from_recipe(recipe))
        fingerprint = manifest.get("fingerprint")
        if not isinstance(fingerprint, dict):
            return False, "manifest fingerprint is missing"
        expected_wav = fingerprint.get("wav_sha256")
        if result.wav_sha256 != expected_wav:
            return False, "re-rendered WAV hash differs (runtime or source mismatch)"
        if result.manifest != manifest:
            return False, "WAV matches but manifest identity differs"
        return True, f"verified {result.wav_sha256}"
    except (
        AttributeError,
        KeyError,
        OSError,
        OverflowError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        return False, str(error)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sonification",
        description="Deterministic, sample-free mathematical loop generator",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="render a loop and provenance artifacts")
    generate.add_argument("--bpm", type=float, default=128.0, dest="tempo_bpm")
    generate.add_argument("--bars", type=int, default=4)
    generate.add_argument("--beats-per-bar", type=int, default=4)
    generate.add_argument("--sample-rate", type=int, choices=(44_100, 48_000), default=44_100)
    generate.add_argument("--bit-depth", type=int, choices=(16, 24), default=24)
    generate.add_argument("--a4", type=float, default=432.0, dest="tuning_a4_hz")
    generate.add_argument("--seed", type=int, default=2026)
    generate.add_argument("--peak-dbfs", type=float, default=-3.0)
    generate.add_argument(
        "--voice",
        choices=("hybrid", "additive", "fm", "karplus"),
        default="hybrid",
        dest="voice_mode",
    )
    generate.add_argument("--export", type=_exports, default=_exports("wav,manifest"))
    generate.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    generate.add_argument("--name", type=_safe_name)
    generate.add_argument("--force", action="store_true", help="replace existing artifacts")
    generate.add_argument("-v", "--verbose", action="store_true")

    verify = subparsers.add_parser("verify", help="check integrity and re-render a manifest")
    verify.add_argument("manifest", type=Path)
    verify.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    if args.command == "verify":
        LOGGER.debug("Verifying manifest %s", args.manifest)
        passed, message = _verify(args.manifest)
        print(("PASS " if passed else "FAIL ") + message)
        return 0 if passed else 1

    try:
        config = LoopConfig(
            tempo_bpm=args.tempo_bpm,
            bars=args.bars,
            beats_per_bar=args.beats_per_bar,
            sample_rate=args.sample_rate,
            bit_depth=args.bit_depth,
            tuning_a4_hz=args.tuning_a4_hz,
            seed=args.seed,
            peak_dbfs=args.peak_dbfs,
            voice_mode=args.voice_mode,
        )
        result = render_loop(config)
        LOGGER.debug("Rendered WAV %s", result.wav_sha256)
        written = _write_result(
            result,
            output_dir=args.output_dir,
            name=args.name,
            exports=args.export,
            force=args.force,
        )
    except (OSError, ValueError, TypeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"Rendered {config.bars} bars / {config.frame_count} frames")
    print(f"WAV SHA-256: {result.wav_sha256}")
    for kind, path in sorted(written.items()):
        print(f"{kind}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
