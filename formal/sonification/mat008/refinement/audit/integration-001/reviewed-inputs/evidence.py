"""Run and verify append-only MAT008 source-binding/conformance receipts.

This checks finite executions and recorded bytes. It is not a Python refinement
proof, and the receipt verifier is trusted ordinary Python code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SCHEMA = "sonification-mat008-refinement-execution-v1"
INPUTS = (
    "formal/sonification/mat008/refinement/evidence.py",
    "formal/sonification/mat008/refinement/source_bind.py",
    "formal/sonification/mat008/refinement/SOURCE_BINDING.json",
    "formal/sonification/mat008/SOURCE_BINDING.json",
    "formal/sonification/mat008/lean/Mat008/RunOwnership.lean",
    "formal/sonification/mat008/conformance.py",
    "materials/mat_spec_008.py",
    "tests/test_sonification_formal_mat008_refinement.py",
)
COMMAND_TAILS = (
    ("--version",),
    ("formal/sonification/mat008/refinement/source_bind.py", "--check-worktree"),
    ("-m", "unittest", "discover", "-s", "tests", "-p",
     "test_sonification_formal_mat008_refinement.py", "-v"),
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def committed_inputs(commit: str) -> dict[str, str]:
    require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)), "full baseline commit required")
    result = {}
    for path in INPUTS:
        raw = (ROOT / path).read_bytes()
        committed = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
            check=True,
            capture_output=True,
            timeout=30,
        ).stdout
        require(raw == committed, f"working input differs from baseline commit: {path}")
        result[path] = sha(raw)
    return result


def command_argv(tail: tuple[str, ...]) -> list[str]:
    return [sys.executable, *tail]


def run(out: Path, commit: str) -> int:
    out.mkdir(parents=True, exist_ok=False)
    report: dict[str, object] = {
        "schema": SCHEMA,
        "status": "INCOMPLETE",
        "assurance": "SOURCE_SYNTAX_AND_FINITE_CONFORMANCE_ONLY",
        "REFINEMENT_PROVED": "OPEN",
        "baseline_commit": commit,
        "started_utc": datetime.now(UTC).isoformat(),
        "working_directory": str(ROOT),
        "python": {"executable": sys.executable, "version": sys.version},
        "commands": [],
    }
    try:
        report["input_sha256"] = committed_inputs(commit)
        commands = report["commands"]
        for index, tail in enumerate(COMMAND_TAILS):
            argv = command_argv(tail)
            timed_out = False
            try:
                result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=120)
                stdout, stderr, exit_code = result.stdout, result.stderr, result.returncode
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                stdout, stderr, exit_code = exc.stdout or b"", exc.stderr or b"", None
            stdout_name, stderr_name = f"{index:02d}.stdout", f"{index:02d}.stderr"
            (out / stdout_name).write_bytes(stdout)
            (out / stderr_name).write_bytes(stderr)
            commands.append({
                "argv": argv,
                "cwd": str(ROOT),
                "exit_code": exit_code,
                "timed_out": timed_out,
                "stdout_path": stdout_name,
                "stdout_sha256": sha(stdout),
                "stderr_path": stderr_name,
                "stderr_sha256": sha(stderr),
            })
            if timed_out or exit_code != 0:
                raise ValueError(f"execution failed at command {index}; raw logs retained")
            if index == 1:
                observed = json.loads(stdout, object_pairs_hook=unique_pairs)
                require(observed.get("status") == "SOURCE_SYNTAX_BINDING_MATCH",
                        "source binder did not report a match")
        report["status"] = "PASS"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report.update(status="FAIL", error=str(exc))
    (out / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "out": str(out), "error": report.get("error")}))
    return 0 if report["status"] == "PASS" else 1


def committed_receipt_bytes(commit: str, path: str) -> bytes:
    require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)),
            "full receipt commit required")
    return subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def verify(out: Path, receipt_commit: str, committed_path: str) -> int:
    prefix = "formal/sonification/mat008/refinement/receipts/"
    path = PurePosixPath(committed_path)
    require(committed_path.startswith(prefix) and ".." not in path.parts
            and str(path) == committed_path, "invalid committed receipt path")
    expected_files = {"result.json"}
    for index in range(len(COMMAND_TAILS)):
        expected_files.update({f"{index:02d}.stdout", f"{index:02d}.stderr"})
    observed = list(out.iterdir())
    require(all(p.is_file() and not p.is_symlink() for p in observed)
            and {p.name for p in observed} == expected_files,
            "retained execution file inventory mismatch")
    for name in sorted(expected_files):
        require((out / name).read_bytes()
                == committed_receipt_bytes(receipt_commit, f"{committed_path}/{name}"),
                f"retained execution file differs from commit: {name}")
    report = json.loads((out / "result.json").read_text(), object_pairs_hook=unique_pairs)
    require(report["schema"] == SCHEMA, "receipt schema mismatch")
    require(report["status"] == "PASS", "receipt does not record PASS")
    require(report["assurance"] == "SOURCE_SYNTAX_AND_FINITE_CONFORMANCE_ONLY",
            "receipt scope changed")
    require(report["REFINEMENT_PROVED"] == "OPEN", "refinement assurance promoted")
    ancestry = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor",
         report["baseline_commit"], receipt_commit],
        capture_output=True,
        timeout=30,
    )
    require(ancestry.returncode == 0,
            "receipt commit does not descend from source input commit")
    require(report["input_sha256"] == committed_inputs(report["baseline_commit"]),
            "receipt source input mismatch")
    commands = report["commands"]
    require(len(commands) == len(COMMAND_TAILS), "execution inventory mismatch")
    for index, (entry, tail) in enumerate(zip(commands, COMMAND_TAILS, strict=True)):
        require(entry["argv"][1:] == list(tail), f"command {index} changed")
        require(entry["cwd"] == report["working_directory"],
                f"command {index} recorded worktree changed")
        require(entry["exit_code"] == 0 and entry["timed_out"] is False,
                f"command {index} failed or timed out")
        for stream in ("stdout", "stderr"):
            name = f"{index:02d}.{stream}"
            require(entry[f"{stream}_path"] == name, f"command {index} {stream} path changed")
            require(sha((out / name).read_bytes()) == entry[f"{stream}_sha256"],
                    f"command {index} {stream} bytes changed")
    observed = json.loads((out / "01.stdout").read_bytes(), object_pairs_hook=unique_pairs)
    require(observed.get("status") == "SOURCE_SYNTAX_BINDING_MATCH",
            "retained source-binder output changed")
    require(observed.get("frozen_source_sha256")
            == "e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08",
            "retained frozen source identity changed")
    print(json.dumps({"status": "EXECUTION_RECEIPT_MATCH", "out": str(out),
                      "receipt_commit": receipt_commit}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="operation", required=True)
    run_parser = subs.add_parser("run")
    run_parser.add_argument("--out", type=Path, required=True)
    run_parser.add_argument("--baseline-commit", required=True)
    verify_parser = subs.add_parser("verify")
    verify_parser.add_argument("receipt", type=Path)
    verify_parser.add_argument("--receipt-commit", required=True)
    verify_parser.add_argument("--committed-path", default=
                               "formal/sonification/mat008/refinement/receipts/conformance-001")
    args = parser.parse_args()
    try:
        if args.operation == "run":
            return run(args.out.resolve(), args.baseline_commit)
        return verify(args.receipt.resolve(), args.receipt_commit, args.committed_path)
    except (KeyError, TypeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
