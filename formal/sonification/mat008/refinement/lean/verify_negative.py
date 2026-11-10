#!/usr/bin/env python3
"""Execute retained-evidence tamper controls on copies, never original evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from functools import partial
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def clone_file(source: Path, target: Path) -> None:
    """Hard links avoid copying a gigabyte; mutations only unlink local names."""
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def clone_toolchain(lean: Path, closure: dict, target: Path) -> None:
    source_root = lean.parent.parent
    clone_file(lean, target / "bin/lean")
    for name in closure:
        relative = "lib/lean/" + name.replace(".", "/") + ".olean"
        clone_file(source_root / relative, target / relative)
    for library in (source_root / "lib/lean").glob("*.so"):
        clone_file(library.resolve(strict=True), target / "lib/lean" / library.name)


def save_change(
    path: Path,
    operation: str,
    content: bytes | None = None,
    *,
    workspace: Path,
    case: Path,
    changes: list[dict],
) -> None:
    before = path.read_bytes()
    label = path.relative_to(workspace).as_posix()
    if content is None:
        path.unlink()
    else:
        path.write_bytes(content)
        saved = case / "changed-files" / label
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(content)
    changes.append(
        {
            "path": label,
            "operation": operation,
            "before_sha256": digest(before),
            "after_sha256": None if content is None else digest(content),
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", required=True, type=Path)
    parser.add_argument("--nominal", type=Path, default=HERE / "attempts/013-checked")
    parser.add_argument("--negative", type=Path, default=HERE / "attempts/014-negative")
    parser.add_argument("--out", required=True, type=Path, help="new directory, never overwritten")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    lean = args.lean.resolve(strict=True)
    closure = json.loads((args.nominal / "toolchain-imports.json").read_text())
    imports = sorted(closure)
    first_import = "lib/lean/" + imports[0].replace(".", "/") + ".olean"
    cases = {
        "unchanged_control": None,
        "relocated_toolchain_control": None,
        "deleted_theorem_declaration": "declaration receipt differs from raw audit",
        "deleted_source_theorem": "nominal source hashes differ",
        "deleted_command_receipt": "execution receipt count mismatch",
        "unimported_source_module": "active source module coverage mismatch",
        "missing_execution_receipt": "missing retained file: verification/result.json",
        "missing_execution_log": "missing retained file: 01.stdout",
        "altered_stdout": "execution stdout hash mismatch",
        "altered_stderr": "execution stderr hash mismatch",
        "missing_import_membership": "toolchain import membership mismatch",
        "missing_local_import": "missing retained file: " + first_import,
        "recorded_import_path_traversal": "recorded import path mismatch",
        "local_import_symlink_escape": "symlink forbidden: " + first_import,
        "missing_negative_receipt": "missing retained file: result.json",
        "altered_negative_stdout": "execution stdout hash mismatch",
        "missing_counterexample_log": "missing retained file: counterexample-0.stdout",
        "altered_counterexample_stderr": "counterexample stderr changed",
    }
    rows = []
    for name, expected in cases.items():
        case = out / name
        case.mkdir()
        with tempfile.TemporaryDirectory(prefix="mat008-retained-tamper-") as temp:
            workspace = Path(temp)
            nominal, negative = workspace / "nominal", workspace / "negative"
            shutil.copytree(args.nominal, nominal)
            shutil.copytree(args.negative, negative)
            effective_lean = lean
            effective_project = HERE
            changes = []
            modify = partial(save_change, workspace=workspace, case=case, changes=changes)

            if name in {
                "relocated_toolchain_control",
                "missing_local_import",
                "local_import_symlink_escape",
            }:
                local_root = workspace / "different-installation-prefix"
                clone_toolchain(lean, closure, local_root)
                effective_lean = local_root / "bin/lean"
                if name != "relocated_toolchain_control":
                    path = local_root / first_import
                    before = digest(path.read_bytes())
                    path.unlink()
                    if name == "local_import_symlink_escape":
                        path.symlink_to(lean.parent.parent / first_import)
                    changes.append(
                        {
                            "path": path.relative_to(workspace).as_posix(),
                            "operation": "unlink"
                            if name == "missing_local_import"
                            else "replace_with_external_symlink",
                            "before_sha256": before,
                        }
                    )
            elif name == "deleted_theorem_declaration":
                path = nominal / "declarations.json"
                rows_before = json.loads(path.read_text())
                value = [
                    row
                    for row in rows_before
                    if row["declaration"] != "Sonification.Mat008.AbstractPy.r7_collision_reason"
                ]
                assert len(value) == len(rows_before) - 1
                modify(path, "delete_r7_declaration", (json.dumps(value, indent=2) + "\n").encode())
            elif name in {"deleted_source_theorem", "unimported_source_module"}:
                effective_project = workspace / "project"
                inputs = json.loads((args.nominal / "result.json").read_text())["input_sha256"]
                for filename in [*inputs, "EVIDENCE_MANIFEST.json"]:
                    target = effective_project / filename
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(HERE / filename, target)
                if name == "deleted_source_theorem":
                    path = effective_project / "Refine/MapReason.lean"
                    text = path.read_text()
                    start = text.index("theorem r7_collision_reason")
                    end = text.index("theorem preexisting_reason_counterexample", start)
                    modify(path, "delete_r7_source_theorem", (text[:start] + text[end:]).encode())
                else:
                    path = effective_project / "Unimported.lean"
                    path.write_text("theorem excluded : True := by trivial\n")
                    saved = case / "changed-files/project/Unimported.lean"
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, saved)
                    changes.append(
                        {
                            "path": "project/Unimported.lean",
                            "operation": "add_unimported_module",
                            "after_sha256": digest(path.read_bytes()),
                        }
                    )
            elif name == "deleted_command_receipt":
                path = nominal / "result.json"
                value = json.loads(path.read_text())
                value["commands"].pop()
                modify(
                    path,
                    "delete_audit_execution_receipt",
                    (json.dumps(value, indent=2) + "\n").encode(),
                )
            elif name == "missing_execution_receipt":
                modify(negative / "weaker_r4_theorem/verification/result.json", "unlink")
            elif name == "missing_execution_log":
                modify(nominal / "01.stdout", "unlink")
            elif name in {"altered_stdout", "altered_stderr"}:
                path = nominal / ("03.stdout" if name == "altered_stdout" else "01.stderr")
                modify(path, "append", path.read_bytes() + b"tampered log\n")
            elif name == "missing_import_membership":
                path = nominal / "toolchain-imports.json"
                value = json.loads(path.read_text())
                del value[imports[0]]
                modify(
                    path, "delete_import_membership", (json.dumps(value, indent=2) + "\n").encode()
                )
            elif name == "recorded_import_path_traversal":
                path = nominal / "toolchain-imports.json"
                value = json.loads(path.read_text())
                value[imports[0]]["path"] = "../../outside/Init.olean"
                modify(
                    path, "traverse_recorded_path", (json.dumps(value, indent=2) + "\n").encode()
                )
            elif name == "missing_negative_receipt":
                modify(negative / "result.json", "unlink")
            elif name == "altered_negative_stdout":
                path = negative / "weaker_r4_theorem/verification/03.stdout"
                modify(path, "append", path.read_bytes() + b"tampered negative log\n")
            elif name == "missing_counterexample_log":
                modify(negative / "reason_erasure/counterexample-0.stdout", "unlink")
            elif name == "altered_counterexample_stderr":
                path = negative / "reason_erasure/counterexample-1.stderr"
                modify(path, "append", b"tampered witness stderr\n")
            argv = [
                sys.executable,
                str(HERE / "verify.py"),
                "--lean",
                str(effective_lean),
                "--lean-root",
                str(effective_lean.parent.parent),
                "--project",
                str(effective_project),
                "--nominal",
                str(nominal),
                "--negative",
                str(negative),
                "--out",
                str(case / "verification"),
            ]
            run = subprocess.run(argv, capture_output=True, timeout=180)
            (case / "runner.stdout").write_bytes(run.stdout)
            (case / "runner.stderr").write_bytes(run.stderr)
            receipt = json.loads((case / "verification/result.json").read_text())
            if expected is None:
                detected = run.returncode == 0 and receipt["status"] == "PASS"
            else:
                detected = (
                    run.returncode == 1
                    and receipt["status"] == "FAIL"
                    and expected in receipt.get("error", "")
                )
            rows.append(
                {
                    "control": name,
                    "argv": argv,
                    "exit_code": run.returncode,
                    "expected_error": expected,
                    "observed_error": receipt.get("error"),
                    "detected": detected,
                    "changes": changes,
                    "runner_stdout_sha256": digest(run.stdout),
                    "runner_stderr_sha256": digest(run.stderr),
                }
            )
    status = "PASS" if all(row["detected"] for row in rows) else "FAIL"
    report = {
        "status": status,
        "assurance": "EVIDENCE_INTEGRITY_CONTROLS_ONLY",
        "REFINEMENT_PROVED": "OPEN",
        "verifier_sha256": digest((HERE / "verify.py").read_bytes()),
        "control_runner_sha256": digest(Path(__file__).read_bytes()),
        "positive_controls": 2,
        "tamper_controls": len(rows) - 2,
        "results": rows,
    }
    (out / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {"status": status, "detected": sum(row["detected"] for row in rows), "total": len(rows)}
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
