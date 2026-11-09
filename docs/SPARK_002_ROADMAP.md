# SPARK-002 proposed roadmap — bounded evidence-kernel verification

Status: **Phase 1A merged with 23/23 reported checks proved; Phase 1B merged with 9/9 reported checks proved by a separate owner-executed strict GNATprove run.** See
[SPARK-002 Phase 1A specification](SPARK_002_SPEC.md).

SPARK-002 would be a separately versioned software-verification project. It
must not alter the frozen MAT-SPEC-010 source, artifacts, claims, release tag
or scientific admission outcomes. In particular, formal verification of
bounded software operations cannot upgrade the blocked independent physical
evidence gates.

## Objective

Investigate a small Ada/SPARK kernel for deterministic numerical and
provenance decisions used by MAT-SPEC-007 through MAT-SPEC-010. The design
should favour exact bounded integers, explicit discriminants, fixed-capacity
records and total fail-closed functions. It should avoid attempting to prove
the Python implementation wholesale.

The owner has authorized a bounded Phase 1A candidate implementation alongside
the written specification, traceability matrix and finite-domain model.
The separate owner-executed strict GNATprove run at merge commit `06b1294bf1617e9eb3b825051e8bfbf7470e395c` passed and its source-pinned receipts are preserved in `publication/spark-002/phase-1a/`. Native Ada/Python CI is not a substitute for formal verification, and neither software result authenticates the physical evidence.

The Phase 1B candidate adds an isolated `Spark_002_Partition` package for a
fixed eight-row campaign-wide TRAIN/HOLDOUT audit and typed missingness
comparisons. See [Phase 1B implementation specification](SPARK_002_PHASE_1B.md).
The Phase 1B owner-executed strict GNATprove run at merged commit
`6f0f1be1ba8885fa708d7328bcb92fbf4ecc324f` reported 9/9 checks proved
(2 functional contracts, 7 termination, no unproved checks), exit status 0.
The seven byte-preserved original receipts and verifier are in
[Phase 1B proof preservation](../publication/spark-002/phase-1b/README.md).
Native Ada/Python CI did not rerun GNATprove. The result establishes only the
declared bounded Ada/SPARK properties, not experimental authentication.

## Candidate proof domains

### 1. Exact fitted-parameter intervals

Represent signed decimal fit values and errors as bounded integers at a
declared power-of-ten scale. Candidate properties:

- interval construction never overflows within the admitted range;
- lower bound is no greater than upper bound;
- overlap includes boundary touching;
- pair ordering is exhaustive and mutually exclusive: below, above, overlap,
  missing or invalid;
- positive scaling preserves ordering and overlap; and
- reversal controls change association without changing the admitted value
  multiset.

This can verify the bounded arithmetic semantics used by MAT-SPEC-007. It
cannot prove that published fit errors are comparable confidence intervals or
that the fitted models are physically correct.

### 2. Bounded decimal and rational conversion

Candidate properties:

- accepted decimal syntax maps to one exact scaled integer;
- malformed, overlong or out-of-range input fails closed;
- negative zero canonicalizes to zero without becoming missing;
- bounded numerator/denominator construction preserves sign and rejects a
  zero denominator;
- cross-multiplication comparisons do not overflow under proved bounds; and
- roundtrip formatting is exact for the admitted canonical subset.

A complete grammar-equivalence theorem would require a stronger parser
contract than SPARK-001 and must be stated explicitly if attempted.

### 3. Missingness and boundary-zero semantics

Use an explicit discriminated value type such as `Missing`, `Measured`,
`Limit_Zero` and `Invalid`. Candidate properties:

- no missing/invalid value is silently converted to numeric zero;
- a declared physical boundary zero remains distinguishable from an absent
  observation;
- comparisons involving missing/invalid data return only the declared
  fail-closed result; and
- serialization tags are injective within the bounded representation.

These properties verify software distinctions, not whether a source author
intended a particular missingness interpretation.

### 4. TRAIN/HOLDOUT source-family partition invariants

Represent fixed-capacity campaign records with bounded identifiers. Candidate
properties:

- each campaign is assigned wholly to one partition;
- no campaign, laboratory family, run identifier, document identifier,
  measurement hash or diagnostic hash crosses TRAIN/HOLDOUT boundaries;
- both declared phase classes are present in each partition before structural
  admission;
- measurement and diagnostic provenance identifiers are separated; and
- empty, padded, malformed or duplicate identifiers are rejected.

A structurally valid record must still return
`STRUCTURAL_ONLY_UNAUTHENTICATED`; the proof cannot authenticate an external
experiment or preregistration.

### 5. Evidence admission and fail-closed decisions

Model the MAT-SPEC-008/009 decision lattice as a total state machine.
Candidate properties:

- every missing prerequisite monotonically prevents physical admission;
- synthetic or secondary evidence can never enter the physical-measurement
  state;
- zero calibrated-uncertainty rows or zero independent diagnostic rows cannot
  produce an admitted classifier score;
- no score exists unless every structural prerequisite is satisfied; and
- invalid state combinations are unreachable through exported operations.

The final state must preserve MAT-SPEC-010's blocked gate for the frozen input.

### 6. Provenance separation and manifest consistency

Candidate properties:

- profile, version, Git tag, commit, DOI and artifact digest occupy distinct
  typed fields and cannot be substituted for one another;
- a foundational DOI cannot be reused as a successor record identity;
- logical paths are unique, relative and traversal-free;
- manifest members are unique and counts agree with bounded arrays;
- every output receipt references an existing declared member; and
- manifest self-hash exclusions are explicit and non-circular.

### 7. Deterministic archived numerical transformations

Candidate properties for a bounded validation kernel:

- canonical sorting produces one order for unique paths;
- every declared transformation consumes only admitted exact values;
- stage counters and artifact-membership counts are conserved;
- the 63 MAT-SPEC-001–009 logical artifact identities map one-to-one to
  materialized archive members; and
- prohibited rendered-audio requests and extensions fail before output.

SPARK may validate digest syntax, equality and manifest linkage. It should not
implement SHA-256 unless that separate cryptographic scope is justified.

## Provable software properties versus external claims

| Domain | Candidate SPARK guarantee | Explicitly outside the proof |
|---|---|---|
| Exact arithmetic | No bounded overflow; exact order/overlap result | Correctness of published physical values |
| Parsing | Declared bounded grammar and total rejection | Equivalence to every external parser or format |
| Missingness | Typed separation of missing, zero and invalid | Source author's physical intent |
| Partitioning | No identifier leakage in admitted records | Actual independence of laboratories or campaigns |
| Admission | Fail-closed state transition logic | Authentication of evidence or preregistration |
| Provenance | Typed identity separation and manifest consistency | Cryptographic authenticity, custody or authorship |
| Archive validation | Deterministic bounded receipt checks | Empirical physics, perceptual results or causality |

## Cryptography and external authentication boundary

SPARK-002 may compare caller-supplied fixed-length SHA-256 values and prove
that mismatches fail closed. Such comparison does not prove that bytes were
obtained from the claimed source. Hash computation, signature verification,
certificate validation, DOI resolution, GitHub/Zenodo account state and
external timestamping remain separate components requiring their own threat
models and evidence.

## Empirical boundary

No formal result from SPARK-002 can demonstrate:

- an independent helium measurement campaign;
- calibrated physical uncertainty or covariance;
- source-separated phase-classifier performance;
- experimental phase labels or physical authenticity;
- human listening or perception outcomes; or
- E8 physical theory.

The frozen MAT-SPEC-010 result remains
`NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES`.

## Proposed staged work

1. Freeze a requirements-to-MAT-SPEC traceability table and exact finite
   bounds. No Ada implementation yet.
2. Review integer ranges, identifier capacities, discriminants and invalid
   states with an independent reviewer.
3. Implement pure packages with contracts and negative compile/runtime tests.
4. Create an independent Python or other reference oracle for differential
   execution. Treat it as testing, not proof.
5. Execute strict GNATprove with pinned versions, warnings as errors, retained
   logs, source hashes and explicit assumption review.
6. Publish only the properties actually discharged, with parser, driver,
   cryptographic and empirical exclusions repeated in release metadata.

## Publication lineage options

After implementation and successful independent review, SPARK-002 could be:

- a distinct related Zenodo Software record when its specification and scope
  are materially separate; or
- a new version in the SPARK-001 software record lineage when Zenodo versioning
  accurately represents an expanded successor of the same kernel.

The choice must be made before publication. Neither option permits rewriting
SPARK-001 v1.0.0 or any MAT-SPEC release.
