# SPARK-001 v1.0.0 Zenodo software archive

This package preserves the exact source and proof receipts for the completed
GitHub release:

- Release: `SPARK-001 v1.0.0 — Formally Verified Bounded Numerical Kernel`
- Git tag: `spark-001-v1.0.0`
- Peeled commit: `95cc7c455535c1c4562d4241f5b387c811d90e5d`
- GitHub release ID: `439229831`
- GitHub publication: `2026-11-09T14:39:06Z`
- Proof evidence asset: `SPARK-001-v1.0.0-proof-evidence.zip`
- Evidence SHA-256: `69ae22cf1e88407c26e98e657ec80b92aba89b28f7bbd683887266e4dd0f23d8`

## Verified result

The owner-executed strict GNATprove FSF 16.1.0 process recorded exit status 0
and discharged all 26 reported checks:

- 18 runtime checks;
- 2 functional contract checks; and
- 6 termination checks.

The receipt reports zero justified checks, zero unproved checks and zero
`pragma Assume` statements. The native Ada/Python differential workflow passed
372 deterministic vectors in GitHub Actions. Differential testing is execution
evidence, not formal proof.

## Formal scope and explicit limitations

Only the declared Ada/SPARK `Spark_Core` properties in the pinned source are
covered by the proof receipts.

- `Spark_Probe` has `SPARK_Mode => Off` and is outside formal analysis.
- The current parser postcondition is not a complete grammar-equivalence
  theorem.
- Source identifier and hash comparisons detect mismatch but do not establish
  external cryptographic authenticity or experimental custody.
- No independent helium physical phase validation was performed.
- No E8 physical theory, auditory-perception result or material classifier is
  established.
- Formal software proof is not physical experimental validation.

## Contents and verification

- `source/` contains the exact relevant source, workflows, tests and scope
  documentation extracted from the immutable release tag.
- `evidence/SPARK-001-v1.0.0-proof-evidence.zip` is the unmodified GitHub
  release asset.
- `evidence/expanded/` exposes the same proof receipts and retained failure
  history for inspection.
- `provenance/source-manifest.json` binds included source bytes to the tagged
  tree.
- `provenance/archive-manifest.json` and `provenance/SHA256SUMS` bind the
  primary archive's payload.

The archive builder verifies the outer evidence SHA-256, both checksum files
inside the proof asset, all three SPARK source hashes, the source commit, proof
counts, formal-scope exclusion and extraction checksums.

```sh
UV_CACHE_DIR=/tmp/qsol-spark-uv \
  uv run --python 3.11 --no-project python \
  scripts/build_spark_001_archive.py \
  --evidence /path/to/SPARK-001-v1.0.0-proof-evidence.zip \
  --out dist/SPARK-001-v1.0.0-zenodo-software.zip

UV_CACHE_DIR=/tmp/qsol-spark-uv \
  uv run --python 3.11 --no-project python \
  scripts/build_spark_001_archive.py --verify-only \
  --out dist/SPARK-001-v1.0.0-zenodo-software.zip
```

The ZIP uses canonical member order, fixed timestamps and file modes, and
`ZIP_STORED`. No rendered or sampled audio is generated or included.

## Publication state

This primary ZIP is prepared for a distinct Zenodo **Software** record. It is
not a new ETQ-303 version and is not a MAT-SPEC-001 version. No Zenodo record
ID or DOI is claimed until Zenodo actually assigns one. Publication requires
owner approval.

