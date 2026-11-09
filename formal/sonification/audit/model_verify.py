#!/usr/bin/env python3
"""Check retained independent audit binding; no semantic claim promotion."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT_SHA256 = "4d4a24100e5ab6015b762204cce4bd2ea660bbd54be5a291ec035e51687b5020"
SNAPSHOT_SOURCE_COMMIT = "fcce6b0d6287a443282013e04b8e7211e1b36eb2"
SNAPSHOT_TREE = "455099b3e40099eac67c810229f5d540ebecfe59"
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
LEAN_VERSION_STDOUT_SHA256 = "5362a246ce2545424db10a77de8fd4694f4cf8b0170dfd43fa727acf7f7f259b"
EXPECTED_AUDIT_SHA256 = "6604bdf24e72d2a307c19581756ca90df9dc7f68553462f9dfb5c54747e29c52"
EXPECTED_MUTATIONS = frozenset({
    "false_theorem",
    "weaker_theorem",
    "hidden_data_sorry",
    "custom_axiom",
    "unimported_nested_module",
    "missing_import",
    "empty_zero_exit_report",
    "missing_expected_inventory",
})
PREFLIGHT_REJECTIONS = frozenset({
    "missing_expected_inventory",
    "unimported_nested_module",
})
EXPECTED_CHECKER_RESULT_SHA256 = {
    "custom_axiom/checker/result.json": (
        "86a2d25bd03153874c1f729946c6d325618bae770b8977ca557d2cf7a9b1e3ff"
    ),
    "empty_zero_exit_report/checker/result.json": (
        "bc56dc7eea63380db9a565c7f2352d4a8286a0ffe76503501d31d7527081defc"
    ),
    "false_theorem/checker/result.json": (
        "a8fa0956adf921794a62946490278e4e042a81ebb475ea58e66ba97afad9eeef"
    ),
    "hidden_data_sorry/checker/result.json": (
        "254f3ae61ec64b340fe2489e329748a6deff6e60b65240e6f3e0fb12e1d79308"
    ),
    "missing_expected_inventory/checker/result.json": (
        "708cf0ae4922bd1faa6df9db7a867ddc68ee48012574d5f4a3671f8246265f5f"
    ),
    "missing_import/checker/result.json": (
        "c789edde8606290daca3cb815f861a731194b0a25e9e9b2828074cec5ad81e55"
    ),
    "nominal-build/result.json": (
        "deb1ab28a88db2f311182f333f4213c26307e49a2acb058ece0687a2758f9c4d"
    ),
    "unimported_nested_module/checker/result.json": (
        "504aea4fdfc6b18958d168853b1ef3b8755b41286b9447c42fb96850c56e124a"
    ),
    "weaker_theorem/checker/result.json": (
        "62e1986e66c461047d9ad02026c6b3d95d02e7fad2c5960ab15dfbebdebc265d"
    ),
}
EXPECTED_NOMINAL_ARTIFACT_SHA256 = {
    "declarations.json": "b1c08f4398b981f7eb988add5d4f91cfe32c4ead5ef1e4028de073de882a7ba9",
    "toolchain-imports.json": "8ffe3ac72c6480936ba701e02ca4e848f8aed9e0fcf5439fb909ede3898138cb",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_retained_snapshot(attempt: Path) -> None:
    """Require all 190 retained model-audit files from merged PR #42."""
    manifest_path = HERE / "attempt-004-model.snapshot.json"
    if attempt.is_symlink() or manifest_path.is_symlink():
        raise ValueError("linked retained model audit root or manifest")
    if digest(manifest_path) != SNAPSHOT_SHA256:
        raise ValueError("retained model audit snapshot manifest changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = manifest["files"]
    if (
        manifest["source_commit"] != SNAPSHOT_SOURCE_COMMIT
        or manifest["source_tree"] != SNAPSHOT_TREE
        or manifest["attempt"] != "attempt-004-model"
        or manifest["expected_file_count"] != 190
        or len(expected) != 190
    ):
        raise ValueError("unexpected retained model audit snapshot identity")
    observed = set()
    for path in attempt.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"linked retained model audit path: {path}")
        if path.is_file():
            observed.add(path.relative_to(attempt).as_posix())
        elif not path.is_dir():
            raise ValueError(f"unsupported retained model audit path: {path}")
    if observed != set(expected):
        raise ValueError("retained model audit file inventory mismatch")
    for relative, expected_hash in expected.items():
        if digest(attempt / relative) != expected_hash:
            raise ValueError(f"altered retained model audit file: {relative}")


def main() -> int:
    attempt = HERE / "attempt-004-model"
    if digest(attempt / "AUDIT.json") != EXPECTED_AUDIT_SHA256:
        raise ValueError("recorded independent audit report changed")
    report = json.loads((attempt / "AUDIT.json").read_text())
    if report["status"] != "PASS" or not report["inputs_stable_during_audit"]:
        raise ValueError("audit incomplete")
    for name, expected in report["proof_input_sha256"].items():
        if digest(HERE.parent / "lean" / name) != expected:
            raise ValueError(f"stale audited input: {name}")
        if digest(attempt / "inputs" / (name + ".source")) != expected:
            raise ValueError(f"altered audited input snapshot: {name}")
    if digest(HERE / "model_run.py") != report["audit_runner_sha256"]:
        raise ValueError("stale audit runner")
    if len(report["theorems"]) != 19 or any(
        row["AUDIT_ACCEPTED"] != "PASS" or row["REFINEMENT_PROVED"] != "OPEN"
        for row in report["theorems"]
    ):
        raise ValueError("unexpected theorem/assurance inventory")
    checks = report["checks"]
    mutations = [c["mutation"] for c in checks if "mutation" in c]
    nominals = [c for c in checks if "mutation" not in c]
    if (
        len(checks) != 9
        or len(nominals) != 1
        or len(mutations) != len(EXPECTED_MUTATIONS)
        or frozenset(mutations) != EXPECTED_MUTATIONS
        or not nominals[0]["expected_zero"]
        or any(c["expected_zero"] for c in checks if "mutation" in c)
        or any(not c["detected_as_expected"] for c in checks)
    ):
        raise ValueError("incomplete negative controls")

    expected_receipts = {
        (Path(c["mutation"]) / "command" / "execution.json")
        if "mutation" in c else Path("nominal-command/execution.json"): c
        for c in checks
    }
    observed_receipts = {path.relative_to(attempt) for path in attempt.rglob("execution.json")}
    if observed_receipts != set(expected_receipts):
        raise ValueError("missing or unexpected audit execution receipts")
    for relative, recorded in expected_receipts.items():
        directory = attempt / relative
        command = json.loads(directory.read_text())
        for field in (
            "argv", "cwd", "exit_code", "expected_zero", "detected_as_expected",
            "stdout_sha256", "stderr_sha256",
        ):
            if command[field] != recorded[field]:
                raise ValueError(f"audit execution mismatch: {directory}: {field}")
        for stream in ("stdout", "stderr"):
            if digest(directory.parent / (stream + ".log")) != recorded[stream + "_sha256"]:
                raise ValueError(f"altered command stream: {directory}")

    expected_results = {Path("nominal-build/result.json"): "PASS"}
    expected_results.update({
        Path(name) / "checker" / "result.json": "FAIL"
        for name in EXPECTED_MUTATIONS
    })
    if {relative.as_posix() for relative in expected_results} != set(
        EXPECTED_CHECKER_RESULT_SHA256
    ):
        raise ValueError("checker result inventory differs from pinned receipts")
    observed_results = {path.relative_to(attempt) for path in attempt.rglob("result.json")}
    if observed_results != set(expected_results):
        raise ValueError("missing or unexpected audit checker results")
    for relative, expected_status in expected_results.items():
        path = attempt / relative
        if digest(path) != EXPECTED_CHECKER_RESULT_SHA256[relative.as_posix()]:
            raise ValueError(f"altered checker result: {path}")
        result = json.loads(path.read_text())
        if result["status"] != expected_status:
            raise ValueError(f"unexpected checker result: {path}")
        if relative.parts[0] in PREFLIGHT_REJECTIONS:
            if result["commands"] or "version" in result:
                raise ValueError(f"unexpected preflight checker content: {path}")
        elif (
            result["version_exit_code"] != 0
            or digest(path.parent / "version.stdout") != LEAN_VERSION_STDOUT_SHA256
            or digest(path.parent / "version.stderr") != EMPTY_SHA256
        ):
            raise ValueError(f"altered checker version output: {path}")
        for check in result["commands"]:
            for stream in ("stdout", "stderr"):
                log = path.parent / check[stream + "_path"]
                if digest(log) != check[stream + "_sha256"]:
                    raise ValueError(f"altered checker stream: {log}")
    nominal = json.loads((attempt / "nominal-build/result.json").read_text())
    for name, expected in EXPECTED_NOMINAL_ARTIFACT_SHA256.items():
        if digest(attempt / "nominal-build" / name) != expected:
            raise ValueError(f"altered nominal proof artifact: {name}")
    if (
        len(nominal["expected_theorems"]) != len(report["theorems"])
        or len(nominal["observed_theorems"]) != len(report["theorems"])
        or set(nominal["expected_theorems"]) != {
            row["declaration"] for row in report["theorems"]
        }
        or set(nominal["observed_theorems"]) != set(nominal["expected_theorems"])
    ):
        raise ValueError("nominal checker theorem inventory changed")
    verify_retained_snapshot(attempt)
    print(json.dumps({"status": "MODEL_AUDIT_BINDING_MATCH", "theorems": 19,
                      "refinement": "OPEN", "scope": "recorded mathematical statements"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
