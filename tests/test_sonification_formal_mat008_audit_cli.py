"""Portable toolchain binding and fail-closed MAT008 audit command controls."""

from __future__ import annotations

import errno
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from formal.sonification.mat008.audit import hotfix_verify, portability_negative
from formal.sonification.mat008.audit import run as audit_run
from formal.sonification.mat008.audit import verify as audit_verify

ROOT = Path(__file__).resolve().parents[1]
LEAN_DIR = ROOT / "formal/sonification/mat008/lean"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def toy_toolchain(base: Path) -> tuple[Path, list[tuple[Path, dict]], set[str], str]:
    """A relocated installation whose recorded original root does not exist."""
    local = base / "relocated-lean"
    (local / "bin").mkdir(parents=True)
    (local / "lib/lean/Std").mkdir(parents=True)
    binary = b"exact-test-lean-binary"
    (local / "bin/lean").write_bytes(binary)
    contents = {"Init": b"exact-init-olean", "Std.Core": b"exact-std-core-olean"}
    historical_root = base / "absent-original-auditor-toolchain"
    imports = {}
    for name, raw in contents.items():
        relative = Path("lib/lean") / (name.replace(".", "/") + ".olean")
        (local / relative).write_bytes(raw)
        imports[name] = {
            "path": str(historical_root / relative),
            "sha256": digest(raw),
        }
    nominal = []
    for name in ("first", "second"):
        root = base / name
        root.mkdir()
        (root / "toolchain-imports.json").write_text(json.dumps(imports))
        nominal.append((root, {"lean_executable": {"path": str(historical_root / "bin/lean")}}))
    return local, nominal, set(contents), digest(binary)


class Mat008PortableAuditTests(unittest.TestCase):
    def test_retained_hotfix_snapshot_rejects_missing_and_extra_evidence(self) -> None:
        self.assertEqual(hotfix_verify.verify()["status"], "HOTFIX_RECEIPTS_MATCH")
        for mutation in (
            "missing_log", "extra_directory", "linked_log", "changed_runner", "changed_test"
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                copied = Path(temp) / "formal/sonification/mat008/audit"
                copied.mkdir(parents=True)
                source = ROOT / "formal/sonification/mat008/audit"
                for name in ("binder-hardening-002", "portability-002"):
                    shutil.copytree(source / name, copied / name)
                for name in (
                    "verify.py", "binder_negative.py", "portability_negative.py",
                    "hotfix-snapshot.json", "run.py",
                ):
                    shutil.copyfile(source / name, copied / name)
                tests = Path(temp) / "tests"
                tests.mkdir()
                shutil.copyfile(
                    ROOT / "tests/test_sonification_formal_mat008_audit_cli.py",
                    tests / "test_sonification_formal_mat008_audit_cli.py",
                )
                old = copied / "attempt-001/fresh-checker"
                old.mkdir(parents=True)
                shutil.copyfile(
                    source / "attempt-001/AUDIT.json", copied / "attempt-001/AUDIT.json"
                )
                shutil.copyfile(
                    source / "attempt-001/fresh-checker/toolchain-imports.json",
                    old / "toolchain-imports.json",
                )
                log = copied / "binder-hardening-002/baseline/stdout"
                if mutation == "missing_log":
                    log.unlink()
                elif mutation == "extra_directory":
                    (copied / "portability-002/unrecorded-empty").mkdir()
                elif mutation == "linked_log":
                    backup = copied / "outside-log"
                    log.rename(backup)
                    log.symlink_to(backup)
                elif mutation == "changed_runner":
                    (copied / "run.py").write_text("raise SystemExit(0)\n")
                else:
                    (tests / "test_sonification_formal_mat008_audit_cli.py").write_text(
                        "# disabled audit CLI tests\n"
                    )
                with patch.object(hotfix_verify, "HERE", copied), self.assertRaises(ValueError):
                    hotfix_verify.verify()

    def test_relocation_copy_fallback_across_filesystems(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.olean"
            target = Path(temp) / "target.olean"
            source.write_bytes(b"exact imported bytes")
            with patch.object(
                portability_negative.os, "link", side_effect=OSError(errno.EXDEV, "cross-device")
            ):
                portability_negative.mirror_file(source, target)
            self.assertEqual(target.read_bytes(), source.read_bytes())

    def test_relocated_identical_toolchain_passes_without_original_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            local, nominal, modules, binary_sha = toy_toolchain(Path(temp))
            self.assertFalse((Path(temp) / "absent-original-auditor-toolchain").exists())
            with patch.object(audit_verify, "EXPECTED_IMPORT_COUNT", 2):
                self.assertEqual(
                    audit_verify.verify_local_toolchain(local, nominal, modules, binary_sha),
                    2,
                )

    def test_toolchain_member_binary_and_path_mutations_fail(self) -> None:
        mutations = {
            "missing_import": lambda local, nominal: (local / "lib/lean/Init.olean").unlink(),
            "changed_import": lambda local, nominal: (
                local / "lib/lean/Init.olean"
            ).write_bytes(b"changed"),
            "changed_binary": lambda local, nominal: (local / "bin/lean").write_bytes(
                b"same-version-banner-but-different-binary"
            ),
            "recorded_path": lambda local, nominal: self.change_recorded_path(nominal[0][0]),
            "missing_member": lambda local, nominal: self.remove_recorded_member(nominal[0][0]),
            "linked_import": lambda local, nominal: self.link_import(local),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                local, nominal, modules, binary_sha = toy_toolchain(Path(temp))
                mutate(local, nominal)
                with (
                    patch.object(audit_verify, "EXPECTED_IMPORT_COUNT", 2),
                    self.assertRaises((OSError, ValueError)),
                ):
                    audit_verify.verify_local_toolchain(local, nominal, modules, binary_sha)

    @staticmethod
    def change_recorded_path(root: Path) -> None:
        path = root / "toolchain-imports.json"
        value = json.loads(path.read_text())
        value["Init"]["path"] = value["Init"]["path"].replace(
            "/Init.olean", "/../Init.olean"
        )
        path.write_text(json.dumps(value))

    @staticmethod
    def remove_recorded_member(root: Path) -> None:
        path = root / "toolchain-imports.json"
        value = json.loads(path.read_text())
        del value["Init"]
        path.write_text(json.dumps(value))

    @staticmethod
    def link_import(local: Path) -> None:
        path = local / "lib/lean/Init.olean"
        copied = local / "lib/lean/Init-copy.olean"
        path.rename(copied)
        path.symlink_to(copied)

    def test_runner_returns_failure_after_retaining_failed_job_receipts(self) -> None:
        cases = {
            "all_success": (None, 0, False, "PASS", 0),
            "failed_job": ("targeted-tests", 7, False, "FAIL", 1),
            "failed_direct_build": ("direct-00", 1, False, "FAIL", 1),
            "failed_version": ("lean-version", 1, False, "FAIL", 1),
            "timed_out_job": ("targeted-tests", None, True, "FAIL", 1),
        }
        for name, (fault, fault_code, fault_timeout, status, exit_code) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                audit_dir = base / "audit"
                audit_dir.mkdir()
                (audit_dir / "independent_conformance.py").write_text("# test input\n")
                toolchain = base / "lean-install"
                (toolchain / "bin").mkdir(parents=True)
                binary = b"pinned-test-binary"
                (toolchain / "bin/lean").write_bytes(binary)

                def fake_git(argv: list[str], cwd: Path) -> bytes:
                    if argv == ["git", "rev-parse", "HEAD"]:
                        return b"f" * 40 + b"\n"
                    source = argv[2].split("/lean/", 1)[1]
                    return (LEAN_DIR / source).read_bytes()

                def fake_capture(
                    out: Path,
                    command: str,
                    argv: list[str],
                    cwd: Path,
                    env=None,
                    fault_name=fault,
                    fault_status=fault_code,
                    fault_timed_out=fault_timeout,
                ) -> dict:
                    broken = command == fault_name
                    code = fault_status if broken else 0
                    timed_out = fault_timed_out if broken else False
                    stdout = f"{command} original test stream\n".encode()
                    (out / f"{command}.stdout").write_bytes(stdout)
                    (out / f"{command}.stderr").write_bytes(b"")
                    record = {
                        "exit_code": code,
                        "timed_out": timed_out,
                        "stdout_path": f"{command}.stdout",
                        "stdout_sha256": digest(stdout),
                        "stderr_path": f"{command}.stderr",
                        "stderr_sha256": digest(b""),
                    }
                    audit_run.write_json(out / f"{command}.json", record)
                    return record

                with (
                    patch.object(audit_run, "HERE", audit_dir),
                    patch.object(audit_run, "ROOT", ROOT),
                    patch.object(audit_run, "LEAN_DIR", LEAN_DIR),
                    patch.object(audit_run, "EXPECTED_LEAN_SHA256", digest(binary)),
                    patch.object(audit_run, "capture", fake_capture),
                    patch.object(audit_run.subprocess, "check_output", fake_git),
                ):
                    observed_exit = audit_run.main(
                        ["new-attempt", "--lean-root", str(toolchain)]
                    )
                attempt = audit_dir / "new-attempt"
                result = json.loads((attempt / "execution-index.json").read_text())
                self.assertEqual(observed_exit, exit_code)
                self.assertEqual(result["status"], status)
                self.assertTrue((attempt / "input-manifest.json").is_file())
                self.assertTrue((attempt / "targeted-tests.stdout").is_file())


if __name__ == "__main__":
    unittest.main()
