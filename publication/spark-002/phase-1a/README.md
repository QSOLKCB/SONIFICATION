# SPARK-002 Phase 1A: owner-executed proof evidence

**Source:** [SONIFICATION PR #36](https://github.com/QSOLKCB/SONIFICATION/pull/36), merged commit `06b1294bf1617e9eb3b825051e8bfbf7470e395c`.

**Formal status:** strict GNATprove FSF 16.1.0 exited 0; 23/23 reported checks proved: 11 functional contracts (CVC5), 12 termination checks (flow); 0 unproved, 0 justified, 0 reported `pragma Assume`. There were no separately reported run-time checks. `Spark_002_Probe` is explicitly outside SPARK mode. See the unmodified owner's `receipts/` files for exact proof output and toolchain.

**Preservation:** all seven original files are committed byte-for-byte, with their digests pinned in the independent, dependency-free verifier. The separately assembled nine-member verified evidence ZIP (not duplicated in Git) has SHA-256 `bc043ad9f676e30a2099905b24d98215826c347754626a1563888f0255e4b9b9`. The `AUDIT.json` file is derived inspection metadata, not an external authenticity attestation.

Run offline from a checkout containing the merge commit:

```sh
uv run --no-project python scripts/verify_spark_002_phase_1a_receipts.py
uv run --no-project python -m unittest tests.test_spark_002_phase_1a_receipts -v
```

This checks original receipt bytes, the six-entry `SHA256SUMS` manifest, exact historical Git source blobs, proof-status text and excluded driver identity. It **does not rerun GNATprove**.

**Scope:** these reported proof checks cover the declared bounded `Spark_002_Core` contracts for exact fit intervals, positive scaling, structural source-identity separation and fail-closed admission decisions. They do not validate physical experiments, independence of labs, the whole Python pipeline, measurements, phase-classifier accuracy, listening outcomes or E8. The frozen MAT-SPEC-010 physical gate remains **blocked**. SPARK-001 and MAT-SPEC tags and releases remain unchanged.

**Publication policy:** no tag, merge, release, Zenodo deposition or scientific-claim promotion is performed by this preservation PR. Review before merging.
