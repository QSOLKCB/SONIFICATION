"""Append-only independent MAT008 proof/evidence audit execution."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LEAN_DIR = HERE.parent / "lean"
PIN = "c7889e3c9468ef4354d45d41b467263a0b5dea02"
LEAN = "/home/trent/.elan/toolchains/leanprover--lean4---v4.19.0/bin/lean"
INPUTS = [
    "Audit.lean", "Mat008.lean", "Mat008/RunOwnership.lean", "check.py",
    "expected-declarations.json", "lakefile.toml", "lean-toolchain", "negative.py",
    "theorem-statements.json",
]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def capture(out: Path, name: str, argv: list[str], cwd: Path, env=None) -> dict:
    began = datetime.now(UTC).isoformat()
    timed_out = False
    try:
        result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=300)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        result = subprocess.CompletedProcess(argv, None, exc.stdout or b"", exc.stderr or b"")
    (out / f"{name}.stdout").write_bytes(result.stdout)
    (out / f"{name}.stderr").write_bytes(result.stderr)
    record = {
        "argv": argv, "cwd": str(cwd), "started_utc": began,
        "exit_code": result.returncode, "timed_out": timed_out,
        "stdout_path": f"{name}.stdout", "stdout_sha256": sha(result.stdout),
        "stderr_path": f"{name}.stderr", "stderr_sha256": sha(result.stderr),
    }
    if env is not None:
        record["explicit_environment"] = {"LEAN_PATH": env["LEAN_PATH"]}
    write_json(out / f"{name}.json", record)
    return record


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 audit/run.py NEW_ATTEMPT_NAME")
    out = HERE / sys.argv[1]
    out.mkdir(exist_ok=False)
    manifest = {
        "proof_input_commit": PIN,
        "checkout_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "input_files": {},
        "audit_runner_sha256": sha(Path(__file__).read_bytes()),
        "independent_conformance_sha256": sha((HERE / "independent_conformance.py").read_bytes()),
        "lean_binary_sha256": sha(Path(LEAN).read_bytes()),
        "python_executable": sys.executable,
        "python_version": sys.version,
    }
    snapshots = out / "inputs"
    snapshots.mkdir()
    for name in INPUTS:
        raw = (LEAN_DIR / name).read_bytes()
        original = subprocess.check_output(
            ["git", "show", f"{PIN}:formal/sonification/mat008/lean/{name}"], cwd=ROOT
        )
        target = snapshots / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        manifest["input_files"][name] = {
            "sha256": sha(raw), "committed_sha256": sha(original), "equal": raw == original,
        }
    write_json(out / "input-manifest.json", manifest)
    assert all(x["equal"] for x in manifest["input_files"].values())
    version = capture(out, "lean-version", [LEAN, "--version"], ROOT)
    direct = []
    with tempfile.TemporaryDirectory(prefix="independent-mat008-") as temp:
        build = Path(temp)
        for module in ("Mat008/RunOwnership.lean", "Mat008.lean", "Audit.lean"):
            target = build / module
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(snapshots / module, target)
        for i, module in enumerate(("Mat008/RunOwnership.lean", "Mat008.lean", "Audit.lean")):
            command = capture(
                out, f"direct-{i:02d}", [LEAN, "-o", module.replace(".lean", ".olean"), module],
                build, {**os.environ, "LEAN_PATH": str(build)},
            )
            direct.append(command)
            if command["exit_code"] != 0:
                break
    jobs = {
        "fresh-checker": [sys.executable, str(LEAN_DIR / "check.py"), "--lean", LEAN,
                          "--out", str(out / "fresh-checker"), "--baseline-commit", PIN],
        "fresh-negative": [sys.executable, str(LEAN_DIR / "negative.py"), "--lean", LEAN,
                           "--out", str(out / "fresh-negative")],
        "submitted-conformance": [sys.executable, str(HERE.parent / "conformance.py"),
                                  "--out", str(out / "submitted-conformance")],
        "independent-conformance": [sys.executable, str(HERE / "independent_conformance.py")],
        "targeted-tests": [sys.executable, "-m", "unittest", "discover", "-s", "tests",
                           "-p", "test_sonification_formal_mat008_run_ownership.py", "-v"],
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {
            name: pool.submit(capture, out, name, argv, ROOT) for name, argv in jobs.items()
        }
        results = {name: future.result() for name, future in futures.items()}
    write_json(out / "execution-index.json", {
        "version": version, "direct_build": direct, "independent_jobs": results,
        "status": "PASS" if len(direct) == 3 and all(
            x["exit_code"] == 0 for x in [version, *direct, *results.values()]
        ) else "FAIL",
    })
    print(json.dumps({"out": str(out), "jobs": {k: v["exit_code"] for k, v in results.items()}}))


if __name__ == "__main__":
    main()
