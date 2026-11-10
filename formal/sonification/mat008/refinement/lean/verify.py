#!/usr/bin/env python3
"""Verify pinned retained abstract-model evidence; no Python refinement claim.

The existing EVIDENCE_MANIFEST is the immutable byte anchor. Independent checks
also relate the receipts, original logs, intended statements and imported files.
Recorded absolute paths are metadata: no original installation path is opened.
The caller chooses a local Lean executable/root with the same pinned bytes.
This is an integrity checker, not a proof of its own correctness or of execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
MANIFEST_SHA256 = "0fcc2432d35fe2c1a93e49da83ef9a5bfd031a41e36f23b74d4e0c66f7997159"
LEAN_SHA256 = "92c3d35b5bfaa5e0fea413a775d504cf46cd95e1345df61c2274f76779e7e023"
DEPENDENCY_SHA256 = "653f4638568e4e461176cca7659360737f3ac2632152163602c789fd65ead201"
DEPENDENCY_COMMIT = "ac1408cf0c459d79c3d0552287812a15ce644f0d"
VERSION = "Lean (version 4.19.0, x86_64-unknown-linux-gnu, commit 6caaee842e94, Release)"
MODULES = ["Mat008.RunOwnership", "Refine.MapReason", "Refine", "Audit"]
SOURCE = "Refine/MapReason.lean"
INPUTS = [
    SOURCE,
    "Refine.lean",
    "Audit.lean",
    "lean-toolchain",
    "lakefile.toml",
    "check.py",
    "negative.py",
    "expected-declarations.json",
    "expected-theorems.json",
    "theorem-statements.json",
]
NOMINAL_ANCHOR = "attempts/013-checked/"
NEGATIVE_ANCHOR = "attempts/014-negative/"
AXIOMS = {"propext", "Quot.sound", "Classical.choice"}
CASES = {
    "update_before_test": (2, "Lean rejected Refine.MapReason"),
    "reason_erasure": (2, "Lean rejected Refine.MapReason"),
    "weaker_r4_theorem": (4, "Lean rejected Audit"),
    "weaker_r7_theorem": (4, "Lean rejected Audit"),
    "prohibited_data_assumption": (4, "Lean rejected Audit"),
    "unimported_module": (0, "module coverage mismatch"),
    "changed_accepted_model": (0, "accepted mathematical dependency source mismatch"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pairs_unique(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def loads(raw: bytes | str):
    return json.loads(raw, object_pairs_hook=pairs_unique)


def member(root: Path, name: str) -> Path:
    """Reject traversal and every symlink below an explicitly chosen root."""
    require(isinstance(name, str), "non-string relative path")
    path = PurePosixPath(name)
    require(
        bool(name)
        and not path.is_absolute()
        and str(path) == name
        and ".." not in path.parts
        and "\\" not in name
        and all(ord(c) >= 32 for c in name),
        f"unsafe relative path: {name!r}",
    )
    root = root.resolve(strict=True)
    current = root
    for part in path.parts:
        current = current / part
        require(not current.is_symlink(), f"symlink forbidden: {name}")
    require(current.is_file(), f"missing retained file: {name}")
    require(current.resolve(strict=True).is_relative_to(root), f"path escapes root: {name}")
    return current


def raw(root: Path, name: str) -> bytes:
    return member(root, name).read_bytes()


def data(root: Path, name: str):
    return loads(raw(root, name))


def file_names(root: Path) -> set[str]:
    root = root.resolve(strict=True)
    result = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), f"symlink forbidden: {path.relative_to(root)}")
        if path.is_file():
            result.add(path.relative_to(root).as_posix())
    return result


def anchored_files(root: Path, anchor: str, manifest: dict) -> None:
    expected = {
        key[len(anchor) :]: value for key, value in manifest.items() if key.startswith(anchor)
    }
    require(bool(expected), "empty retained evidence anchor")
    observed = file_names(root)
    require(observed == set(expected), f"retained file membership mismatch under {anchor}")
    for name, value in expected.items():
        require(digest(raw(root, name)) == value, f"retained file hash mismatch: {anchor}{name}")


def boundary(report: dict, nominal: bool) -> None:
    require(report.get("assurance") == "ABSTRACT_STATE_CORRESPONDENCE_ONLY", "assurance changed")
    require(report.get("python_refinement") == "OPEN", "Python claim boundary changed")
    if nominal or "REFINEMENT_PROVED" in report:
        require(report.get("REFINEMENT_PROVED") == "OPEN", "refinement claim boundary changed")


def dependency(report: dict) -> None:
    dep = report["accepted_mathematical_dependency"]
    require(dep["module"] == MODULES[0], "dependency module changed")
    require(dep["sha256"] == DEPENDENCY_SHA256, "dependency digest changed")
    require(dep["source_commit"] == DEPENDENCY_COMMIT, "dependency source commit changed")


def executions(root: Path, report: dict, count: int, failed: bool) -> str:
    commands = report["commands"]
    require(len(commands) == count, "execution receipt count mismatch")
    combined = ""
    for index, command in enumerate(commands):
        filename = MODULES[index].replace(".", "/") + ".lean"
        argv = command["argv"]
        require(
            argv == [report["lean_executable"]["path"], "-o", filename[:-5] + ".olean", filename],
            f"execution command mismatch at {index}",
        )
        expected_exit = 1 if failed and index == count - 1 else 0
        require(
            type(command["exit_code"]) is int and command["exit_code"] == expected_exit,
            f"execution exit mismatch at {index}",
        )
        require(command["timed_out"] is False, f"timed-out execution at {index}")
        require(command["timeout_seconds"] == 180, "execution timeout contract changed")
        require(
            command["environment"] == {"LEAN_PATH": command["working_directory"]},
            "execution environment mismatch",
        )
        for stream in ["stdout", "stderr"]:
            name = f"{index:02d}.{stream}"
            require(command[f"{stream}_path"] == name, "execution log path mismatch")
            content = raw(root, name)
            require(
                digest(content) == command[f"{stream}_sha256"], f"execution {stream} hash mismatch"
            )
            if stream == "stdout":
                combined += content.decode()
    return combined


def version_receipt(root: Path, report: dict) -> None:
    require(
        report["version_exit_code"] == 0 and report["version"] == VERSION, "version receipt changed"
    )
    require(raw(root, "version.stdout") == (VERSION + "\n").encode(), "version stdout changed")
    require(raw(root, "version.stderr") == b"", "version stderr changed")
    require(
        report["lean_executable"]["sha256"] == LEAN_SHA256, "recorded executable digest changed"
    )


def nominal_evidence(project: Path, root: Path, manifest: dict) -> tuple[dict, dict]:
    report = data(root, "result.json")
    require(report["status"] == "PASS", "nominal receipt is not PASS")
    boundary(report, True)
    dependency(report)
    active = sorted(
        name
        for name in file_names(project)
        if name.endswith(".lean") and not ({"attempts", ".lake"} & set(PurePosixPath(name).parts))
    )
    require(
        active == sorted([SOURCE, "Refine.lean", "Audit.lean"]),
        "active source module coverage mismatch",
    )
    expected_inputs = {name: digest(raw(project, name)) for name in INPUTS}
    require(report["input_sha256"] == expected_inputs, "nominal source hashes differ")
    for name, value in expected_inputs.items():
        require(manifest[name] == value, f"pinned source hash mismatch: {name}")
    version_receipt(root, report)
    audit = executions(root, report, 4, False)
    lines = audit.splitlines()
    declarations = [loads(line[19:]) for line in lines if line.startswith("MAT008_REFINE_DECL ")]
    require(
        declarations == data(root, "declarations.json"),
        "declaration receipt differs from raw audit",
    )
    names = [row["declaration"] for row in declarations]
    require(len(names) == len(set(names)), "duplicate audited declaration")
    require(
        sorted(names) == data(project, "expected-declarations.json"),
        "exact declaration inventory mismatch",
    )
    require(len(declarations) == report["declaration_count"] == 253, "declaration count mismatch")
    for row in declarations:
        require(row["origin"] in MODULES, "declaration origin outside intended modules")
        require(row["kind"] in {"theorem", "non_theorem"}, "declaration kind changed")
        require(type(row["unsafe_definition"]) is bool, "missing declaration safety flag")
        require(isinstance(row["type"], str) and bool(row["type"]), "missing declaration type")
        require(len(row["axioms"]) == len(set(row["axioms"])), "duplicate axiom")
        require(set(row["axioms"]) <= AXIOMS, "prohibited transitive axiom")
    intended = data(project, "expected-theorems.json")
    statements = data(project, "theorem-statements.json")
    require(len(intended) == len(set(intended)) == 26, "intended theorem count mismatch")
    require(
        sorted(row["declaration"] for row in statements) == sorted(intended),
        "statement inventory mismatch",
    )
    observed = {row["declaration"]: row for row in declarations}
    require(
        all(observed.get(row["declaration"]) == row for row in statements),
        "exact theorem statement/axiom mismatch",
    )
    require(
        report["expected_theorems"] == report["observed_theorems"] == sorted(intended),
        "theorem receipt mismatch",
    )
    origins = [line[21:] for line in lines if line.startswith("MAT008_REFINE_MODULE ")]
    require(
        sorted(origins) == sorted(MODULES) == report["imported_modules"], "module coverage mismatch"
    )
    summary = [line for line in lines if line.startswith("MAT008_REFINE_AUDIT ")]
    theorem_count = sum(row["kind"] == "theorem" for row in declarations)
    require(
        summary == [f"MAT008_REFINE_AUDIT declarations=253 theorems={theorem_count}"],
        "audit summary mismatch",
    )
    imports = [line[21:] for line in lines if line.startswith("MAT008_REFINE_IMPORT ")]
    require(len(imports) == len(set(imports)), "duplicate imported module")
    closure = data(root, "toolchain-imports.json")
    require(set(closure) == set(imports) - set(MODULES), "toolchain import membership mismatch")
    original = PurePosixPath(report["lean_executable"]["path"])
    require(
        original.is_absolute() and original.parts[-2:] == ("bin", "lean"),
        "invalid recorded Lean path",
    )
    for name, entry in closure.items():
        require(
            re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*", name) is not None,
            "unsafe module name",
        )
        relative = name.replace(".", "/") + ".olean"
        require(
            entry["path"] == str(original.parent.parent / "lib/lean" / relative),
            "recorded import path mismatch",
        )
        require(re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is not None, "invalid import digest")
    anchored_files(root, NOMINAL_ANCHOR, manifest)
    return report, closure


def negative_evidence(project: Path, root: Path, nominal: dict, manifest: dict) -> None:
    report = data(root, "result.json")
    require(report["status"] == "PASS", "negative-control suite is not PASS")
    require(
        report["scope"] == "Abstract state correspondence only; CPython refinement OPEN.",
        "negative scope changed",
    )
    rows = report["results"]
    require(
        len(rows) == 7 and {row["mutation"] for row in rows} == set(CASES),
        "negative-control inventory mismatch",
    )
    for row in rows:
        name = row["mutation"]
        case = member(root, name + "/MapReason.lean").parent
        count, error = CASES[name]
        require(row["detected"] is True and row["exit_code"] == 1, f"negative not detected: {name}")
        require(row["expected_error"] == error, f"negative expected error changed: {name}")
        require(
            digest(raw(case, "MapReason.lean")) == row["source_sha256"],
            f"mutant source changed: {name}",
        )
        failure = data(case, "verification/result.json")
        boundary(failure, False)
        require(failure["status"] == "FAIL", f"negative verification not failed: {name}")
        require(
            failure["error"].startswith(error) and row["observed_error"] == failure["error"],
            f"negative failure stage changed: {name}",
        )
        if count:
            dependency(failure)
            expected = {**nominal["input_sha256"], SOURCE: row["source_sha256"]}
            require(failure["input_sha256"] == expected, f"negative source binding changed: {name}")
            version_receipt(case / "verification", failure)
            output = executions(case / "verification", failure, count, True)
            marker = {
                "prohibited_data_assumption": "unapproved transitive axiom sorryAx",
                "weaker_r4_theorem": "r4_reason_iff",
                "weaker_r7_theorem": "r7_collision_reason",
            }.get(name, "error:")
            require(marker in output, f"expected negative diagnostic missing: {name}")
        else:
            require(failure["commands"] == [], f"unexpected negative executions: {name}")
        runner = data(case, "runner.stdout")
        require(
            runner["status"] == "FAIL" and runner["error"] == failure["error"],
            f"runner receipt differs: {name}",
        )
        require(raw(case, "runner.stderr") == b"", f"runner stderr changed: {name}")
        argv = row["argv"]
        require(
            len(argv) == 8
            and argv[2] == "--lean"
            and argv[3] == nominal["lean_executable"]["path"],
            "negative runner command changed",
        )
        require(
            argv[4] == "--accepted-model" and argv[6] == "--out",
            "negative runner argument shape changed",
        )
        if name == "reason_erasure":
            witness = row["counterexample"]
            require(
                digest(raw(case, "Counterexample.lean")) == witness["source_sha256"],
                "counterexample source changed",
            )
            require(len(witness["commands"]) == 2, "counterexample execution receipt missing")
            for index, filename in enumerate(["Mat008/RunOwnership.lean", "Counterexample.lean"]):
                command = witness["commands"][index]
                require(command["exit_code"] == 0, "counterexample did not compile")
                require(
                    command["argv"]
                    == [
                        nominal["lean_executable"]["path"],
                        "-o",
                        filename[:-5] + ".olean",
                        filename,
                    ],
                    "counterexample command changed",
                )
                for stream in ["stdout", "stderr"]:
                    require(
                        raw(case, f"counterexample-{index}.{stream}") == b"",
                        f"counterexample {stream} changed",
                    )
    anchored_files(root, NEGATIVE_ANCHOR, manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", required=True, type=Path)
    parser.add_argument(
        "--lean-root",
        type=Path,
        help="local installation root; default resolved executable's grandparent",
    )
    parser.add_argument("--project", type=Path, default=HERE)
    parser.add_argument(
        "--accepted-model", type=Path, default=HERE.parents[1] / "lean/Mat008/RunOwnership.lean"
    )
    parser.add_argument("--nominal", type=Path, default=HERE / "attempts/013-checked")
    parser.add_argument("--negative", type=Path, default=HERE / "attempts/014-negative")
    parser.add_argument(
        "--out", required=True, type=Path, help="new output directory, never overwritten"
    )
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    result = {
        "status": "FAIL",
        "assurance": "RETAINED_ABSTRACT_MODEL_EVIDENCE_INTEGRITY_ONLY",
        "REFINEMENT_PROVED": "OPEN",
        "commands": [],
        "trust": (
            "Reviewed verifier and fixed manifest pin; hashing/OS execution. "
            "This does not authenticate the original execution or rerun proof checking."
        ),
    }
    try:
        manifest_raw = raw(args.project, "EVIDENCE_MANIFEST.json")
        require(
            digest(manifest_raw) == MANIFEST_SHA256, "retained evidence manifest anchor changed"
        )
        manifest = loads(manifest_raw)["files"]
        require(
            digest(args.accepted_model.read_bytes()) == DEPENDENCY_SHA256,
            "accepted mathematical source changed",
        )
        nominal, closure = nominal_evidence(args.project, args.nominal, manifest)
        negative_evidence(args.project, args.negative, nominal, manifest)
        lean = args.lean.resolve(strict=True)
        root = (args.lean_root or lean.parent.parent).resolve(strict=True)
        require(member(root, "bin/lean") == lean, "local Lean executable/root mismatch")
        require(digest(lean.read_bytes()) == LEAN_SHA256, "local Lean executable digest mismatch")
        for name, entry in closure.items():
            relative = "lib/lean/" + name.replace(".", "/") + ".olean"
            require(
                digest(raw(root, relative)) == entry["sha256"],
                f"local toolchain import hash mismatch: {name}",
            )
        command = [str(lean), "--version"]
        run = subprocess.run(command, capture_output=True, timeout=30)
        (out / "local-version.stdout").write_bytes(run.stdout)
        (out / "local-version.stderr").write_bytes(run.stderr)
        result["commands"].append(
            {
                "argv": command,
                "exit_code": run.returncode,
                "stdout_sha256": digest(run.stdout),
                "stderr_sha256": digest(run.stderr),
            }
        )
        require(
            run.returncode == 0 and run.stdout == (VERSION + "\n").encode() and not run.stderr,
            "local Lean version mismatch",
        )
        result.update(
            status="PASS",
            declaration_count=253,
            intended_theorems=26,
            negative_controls=7,
            imported_toolchain_files=len(closure),
            lean_root=str(root),
            manifest_sha256=MANIFEST_SHA256,
            nominal_receipt_sha256=digest(raw(args.nominal, "result.json")),
            negative_receipt_sha256=digest(raw(args.negative, "result.json")),
        )
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result["error"] = str(exc)
    result["verifier_sha256"] = digest(Path(__file__).read_bytes())
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "error": result.get("error"), "out": str(out)}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
