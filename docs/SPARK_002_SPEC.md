# SPARK-002 Phase 1A — Bounded interval and evidence-gate specification

**Status: Phase 1A owner-run GNATprove receipts verified (23/23 reported checks), source-pinned to merged commit `06b1294bf1617e9eb3b825051e8bfbf7470e395c`. The native CI does not itself execute GNATprove. No release or scientific-gate promotion.**

This is a separate Ada/SPARK verification stream. It leaves SPARK-001 v1.0.0,
MAT-SPEC-001–010, historical source data, tags, scientific claims, checksums
and all Zenodo publications unchanged. **No MAT-SPEC-011.**

## Traceability to frozen MAT-SPEC operations

| MAT-SPEC source | SPARK-002 candidate contract | What it does not prove |
|---|---|---|
| 007 `interval`, `classify` | `Make_Box` constructs closed intervals; `Compare` identifies strict below/above or inclusive overlap | Arbitrary precision Python `Fraction` equivalence, source-value correctness or statistics |
| 007 `pairwise_fits` | `Positive_Scale_Preserves_Order` asserts order covariance under positive scaling | Scientific universality or harmonized confidence intervals |
| 008 `validate_future_measurement_packet` | `Has_Identity` and `Pair_Separated` reject absent/colliding coded identities | Authenticity or independence of external experiments |
| 009 source-separated protocol | `Evaluate` blocks missing declared split/phase/uncertainty/diagnostic/registration prerequisites | Whole-dataset proof, real phase labels or preregistration |
| 010 `verify_parent` / `science_closure` | `Frozen_010_Decision` preserves blocked physical admission and absent classifier score | SHA-256 implementation, publication-state verification or physical validation |

This is **bounded contract correspondence**, not a verified semantic refinement
of all Python implementations. In particular, SPARK-002 does not parse JSON,
read experiments, compute digests, run classifiers or render sampled audio.

## Numerical domain (exact, finite)

All interval endpoints are integers interpreted as **millionths** of a
declared nominal unit. No floating-point operations:

- Center: `-4_000_000 .. 4_000_000`
- Error: `0 .. 1_000_000` (zero is a software boundary control; published
  MAT-SPEC-007 fit errors are required to be strictly positive)
- Constructed endpoints: `-5_000_000 .. 5_000_000`
- Positive integer scaling: `1 .. 8`
- Scaled endpoints: `-40_000_000 .. 40_000_000`

The bounded operations fit in a signed 32-bit Ada `Integer` on the pinned
toolchain. A touching interval pair is classified `Overlap`. Invalid values
are rejected by the **non-SPARK** CLI before entering these typed functions.
This micro-unit representation is an authored proof domain, not a claim that
all historical fitted source values have exactly six decimal places.

## Source codes and structural admission

`Identity_Code` is `0 .. 65_535`; zero represents missing. Codes are
supplied by a caller, not authenticated source IDs or actual SHA-256 digests.
A source requires nonzero campaign, lab, original run, original document,
measurement-hash code, diagnostic-hash code, and diagnostic-event code.
Measurement and diagnostic codes for a record must differ.

`Pair_Separated` requires distinct declared roles (TRAIN/HOLDOUT) and all
seven distinct identity fields across the two records. This *conservative
pairwise* check is not a global partition algorithm or proof of laboratory
independence.

`Evaluate` returns either `Blocked` or
`Structural_Only_Unauthenticated`. A structural candidate requires
an original processed source class, at least two declared campaigns and one
pair, positive calibrated-error/independent-diagnostic row counts, both
physical phase labels in both partitions, separated families, a declared
registration receipt, and matching declared experimental conditions.

Even with all bits set, `Physical_Evidence_Admitted` and
`Classifier_Score_Available` are **always False**. Secondary fits, model
inputs, evaluated compilations, synthetic fixtures, missing and invalid
source classes always fail closed. This cannot validate external evidence.

`Frozen_010` explicitly preserves the frozen source audit: one source-pinned
processed campaign, zero independent pairs, zero calibrated uncertainty rows,
zero independent diagnostic rows. The result must remain
`Blocked` with no score and no physical admission.

## Proof obligations (NOT YET DISCHARGED)

- P1. No overflow or out-of-range results in bounded interval construction
  and multiplication.
- P2. Total, mutually exclusive below / above / overlap classification,
  including boundary-touch cases.
- P3. Positive scaling preserves interval classification over every admitted
  typed value, not only selected examples.
- P4. Every gate result is structural at best and has no physical admission
  or classifier score.
- P5. The frozen MAT-SPEC-010 evidence input always yields `Blocked`.
- P6. The pairwise source-code comparison is conservative and never accepts
  absent or colliding identities.

All formal claims require an **actual strict GNATprove run** with source SHA,
toolchain versions, discharged VC counts, assumptions and retained logs.

## Testing and reproduction

The separate `verification/spark002/` Ada package and unproved driver have a
GNAT-13 GitHub-hosted CI workflow. The independent Python stdlib oracle
exercises deterministic boundary and adversarial cases. This is finite
software testing, **not** formal proof or source authenticity.

From a reviewed SONIFICATION checkout:

```sh
uv run --no-project python -m unittest tests.test_spark_002 -v
mkdir -p /tmp/qsol-spark-002
(cd /tmp/qsol-spark-002 && gnatmake -gnat2022 -gnata \
  -I"$HOME/SONIFICATION/verification/spark002" \
  "$HOME/SONIFICATION/verification/spark002/spark_002_probe.adb" \
  -o /tmp/qsol-spark-002/spark_002_probe)
uv run --no-project python scripts/verify_spark_002.py \
  --exe /tmp/qsol-spark-002/spark_002_probe
```

### Manual proof evidence (after review)

The owner can run `bash scripts/run_spark_002_proof.sh` from an inspected
checkout or separate worktree. It uses Alire 2.1.1 + GNATprove, strict
`--mode=all --level=2 --report=statistics --checks-as-errors=on
--warnings=error --proof-warnings=on` and records the actual exit status,
source commit, source hashes, tool versions, proof log, GNATprove report
and a local SHA-256 receipt.

The proof is not run by untrusted pull-request workflows or on the user's
self-hosted workstation without authorization.

**Phase 1A acceptance:** reviewed source, native CI passing and explicit
`SPARK_002_FORMAL_PROOF_STATUS=NOT_EXECUTED` is the native-CI *job* status, not the status of the separately executed owner proof. Historical owner-run proof evidence is preserved in `publication/spark-002/phase-1a/`; no tag/DOI/release.
Later phases may attempt full proofs, stronger parser contracts, a fixed-size
global provenance audit, and independent Python/Ada semantic correspondence.
