# SPARK-002 Phase 1B — Fixed-capacity campaign partition and missingness kernel

**Phase 1B merged; owner-executed GNATprove proof receipts verified (9/9 reported checks) at source commit `6f0f1be1ba8885fa708d7328bcb92fbf4ecc324f`.**
The historical receipts and an offline integrity verifier are preserved in
[publication/spark-002/phase-1b](../publication/spark-002/phase-1b/README.md).
This is not a new prover execution by CI.
This is an extension of SPARK-002, not a new MAT-SPEC profile. Phase 1A
proof receipts (23/23 at `06b1294bf1617e9eb3b825051e8bfbf7470e395c`)
remain source-pinned and unchanged. No SPARK-001 or MAT-SPEC release is modified.

## Traceability and finite representation

| Frozen research source | Phase 1B operation | Conservative boundary |
|---|---|---|
| MAT-SPEC-008 `validate_future_measurement_packet` | All-row nonzero declared identity, campaign consistency, run/document/source-hash ownership | Caller-entered codes cannot authenticate documents, hashes or experiments |
| MAT-SPEC-009 TRAIN/HOLDOUT protocol | Campaign stays in one partition, no shared lab across partitions, both declared phase classes required in each | Not an independent experimental holdout or a physical phase label |
| MAT-SPEC-009 synthetic controls | Synthetic, secondary, unspecified or missing/invalid rows block structural admission | These tests create no actual measurements or classifier accuracy |
| MAT-SPEC-007/-009 boundary/missingness cases | Distinct `Measured`, `Boundary_Zero`, `Missing`, `Invalid`; fail-closed comparison | No interpretation of external missing-value conventions |
| MAT-SPEC-010 closure | `Audit` always returns `Physical_Evidence_Admitted=False`, `Classifier_Score_Available=False` | Scientific gate remains closed and no physical accuracy is calculated |

- **Capacity:** exactly 8 fixed slots; active count 0–8, all unused slots
  must equal `Empty_Row` exactly. No truncation/implicit acceptance of extras.
- **Identifiers:** caller-assigned codes 0–65,535, where **zero is missing**.
  Distinct code values are not cryptographic fingerprints or authenticated IDs.
- **Observations:** signed -1,000,000..1,000,000 (software-scaled nominal
  units); `Boundary_Zero` is usable only at numeric zero. `Measured` zero
  is distinguishable from a declared boundary zero; `Missing` and `Invalid`
  never participate in numerical comparison.
- **Row tags:** TRAIN/HOLDOUT; HE_I/HE_II/UNKNOWN; original-processed,
  secondary-fit, synthetic-fixture and unknown-source. Only a caller-declared
  original-processed, non-missing, calibrated and phase-labelled row can
  satisfy the **structural** row predicate.
- **Every active pair:** distinct row ID; identical registration receipt;
  consistent campaign/role/lab/run/document/measurement-hash metadata within
  one campaign. Across campaigns, run, document, measurement hash, diagnostic
  hash and diagnostic event may not be reused. A hash from the measurement
  domain of one campaign cannot be used as a diagnostic hash in another.
  LAB identities may be shared only within the same TRAIN/HOLDOUT partition.
  Diagnostic identifiers may repeat *within* one declared campaign, as in
  the prospective MAT-SPEC-009 protocol.
- **Admission:** requires at least four rows, an active HE_I and HE_II row
  in each partition, all active rows valid, every inactive slot empty, and
  every active pair compatible. Passing returns only
  `STRUCTURAL_ONLY_UNAUTHENTICATED`; otherwise `BLOCKED`.
- **Untrusted CLI:** the non-SPARK probe rejects bad enum tags, out-of-range
  numbers, extra tokens and invalid booleans as `INVALID`. This wrapper is
  outside the Ada/SPARK proof boundary. The `T` command deliberately corrupts
  an unused slot for a negative padding test.

## Formal proof targets and executed result

The owner-executed strict GNATprove FSF 16.1.0 run at the merged Phase 1B
commit reported **Success: all checks proved (9 checks)** with exit status 0.
The reported checks are **2 functional contracts** (`Compare_Readings` and
`Audit`) and **7 termination checks** (flow), with 0 unproved and 0 justified.
No separately counted runtime checks appear in this summary; the non-SPARK
probe was excluded and no `pragma Assume` statements were reported. The
contract predicates remain authored specifications, not independently proven
experiment identities or a Python semantic-refinement theorem.

The following requirements describe the bounded properties and design targets;
they must not be read as independently discharged, stronger theorems beyond
the actual GNATprove summary:

1. A `STRUCTURAL_ONLY_UNAUTHENTICATED` result implies the defined all-row,
   all-pair and phase-presence predicates.
2. `Audit` has no other physical admission or classifier-score state on any
   well-typed packet, regardless of caller-supplied provenance codes.
3. No `Missing`, `Invalid` or malformed `Boundary_Zero` reading compares as a
   numeric value, even when its stored integer happens to be zero.
4. All returned results and array accesses remain within fixed Ada subtypes.
5. The predicate checks the entire fixed-capacity packet, not just the first
   matching campaign or phase; non-empty padding fails closed.

`Packet_Eligible`, `Compatible`, and `Declared_Row_Valid` are explicit
**authored predicates**. The historical GNATprove run discharged the reported `Audit` postcondition
and termination obligations under the authored predicates; it cannot prove
the external identity codes were assigned faithfully. No universal refinement of MAT-SPEC Python
implementations or complete grammar equivalence is asserted.

## Test and proof workflow

The standard-library Python oracle uses maps of declared campaign/source
owners, independent of the Ada pairwise quantified predicate. Its fixed-seed
adversarial vectors include duplicate IDs, conflicting roles, shared labs,
provenance reuse, unfilled phases, synthetic sources, missing/invalid values,
nonzero boundary-zero tags and malicious inactive padding.

```sh
# From SONIFICATION repository root — Python unit tests only:
uv run --no-project python -m unittest tests.test_spark_002_phase_1b -v

# GitHub-hosted native Ada test workflow compiles with GNAT 13:
# .github/workflows/spark-002-phase-1b.yml

# AFTER reviewed source on a trusted local workstation, manually:
bash scripts/run_spark_002_phase_1b_proof.sh
```

The manual script retains `SOURCE_COMMIT.txt`, exact `SOURCES.sha256`,
toolchain, `PROOF.log`, strict GNATprove exit status, summary (if produced),
prior summary (if present) and a checksum manifest under a unique local
`SPARK-002-1B-*` receipt directory. It never changes Phase 1A receipts.

**Admission rule:** Native differential CI still reports `NOT_EXECUTED_BY_CI`.
The separate strict owner-run proof is recorded and preserved at its exact
merged source identity. Future code changes require their own fresh proof.
The software proof is not independent helium data, calibrated uncertainty,
external source authentication, human perception or E8 physics. The final
MAT-SPEC gate remains `NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES`.
