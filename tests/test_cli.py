"""CLI generation, verification, and tamper-detection integration tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from sonification.cli import main
from sonification.core.provenance import canonical_json_bytes


def test_cli_generates_all_artifacts_verifies_and_rejects_tamper(
    tmp_path: Path,
    capsys: object,
) -> None:
    exit_code = main(
        [
            "generate",
            "--bpm",
            "400",
            "--bars",
            "1",
            "--beats-per-bar",
            "1",
            "--sample-rate",
            "44100",
            "--bit-depth",
            "16",
            "--voice",
            "additive",
            "--seed",
            str((1 << 63) + 9),
            "--export",
            "all",
            "--output-dir",
            str(tmp_path),
            "--name",
            "cli-case",
        ]
    )
    generated_output = capsys.readouterr().out  # type: ignore[attr-defined]

    assert exit_code == 0
    assert "Rendered 1 bars / 6615 frames" in generated_output
    expected_paths = {
        "wav": tmp_path / "cli-case.wav",
        "manifest": tmp_path / "cli-case.manifest.json",
        "recipe": tmp_path / "cli-case.recipe.json",
        "fingerprint": tmp_path / "cli-case.fingerprint.json",
    }
    assert all(path.is_file() and path.stat().st_size > 0 for path in expected_paths.values())
    assert expected_paths["wav"].read_bytes().startswith(b"RIFF")

    manifest = json.loads(expected_paths["manifest"].read_text(encoding="utf-8"))
    assert manifest["recipe"]["render"]["config"]["seed"] == "0x8000000000000009"

    assert main(["verify", str(expected_paths["manifest"])]) == 0
    verified_output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "PASS verified" in verified_output

    manifest["claim_boundary"] += " tampered"
    expected_paths["manifest"].write_bytes(canonical_json_bytes(manifest))

    assert main(["verify", str(expected_paths["manifest"])]) == 1
    tamper_output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "FAIL manifest core integrity check failed" in tamper_output


def test_verify_rejects_non_object_json_without_traceback(tmp_path: Path) -> None:
    path = tmp_path / "list.json"
    path.write_text("[]\n", encoding="utf-8")

    assert main(["verify", str(path)]) == 1


def test_cli_replay_is_exact_across_fresh_processes(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    command = [
        sys.executable,
        "-m",
        "sonification",
        "generate",
        "--bpm",
        "400",
        "--bars",
        "1",
        "--beats-per-bar",
        "1",
        "--sample-rate",
        "44100",
        "--bit-depth",
        "16",
        "--voice",
        "additive",
        "--seed",
        "77",
        "--export",
        "wav,manifest",
        "--name",
        "process-case",
    ]
    environment = {**os.environ, "PYTHONPATH": str(Path.cwd())}
    subprocess.run(
        [*command, "--output-dir", str(first)],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    subprocess.run(
        [*command, "--output-dir", str(second)],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert (first / "process-case.wav").read_bytes() == (second / "process-case.wav").read_bytes()
    assert (first / "process-case.manifest.json").read_bytes() == (
        second / "process-case.manifest.json"
    ).read_bytes()
