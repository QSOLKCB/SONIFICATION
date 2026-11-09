# After MAT-SPEC-010 — Formal verification handoff

**The numbered MAT-SPEC series closes at 010.**
Future work is a separate verification programme, not MAT-SPEC-011,
and cannot retrospectively promote an earlier blocked scientific gate.

## Phase A — SONIFICATION SPARK/Ada proof

Target is a bounded *numerical kernel*, not a theory of physical
phase discrimination. The prospective independently specified
computational contracts are:

1. Exact bounded signed decimal to rational conversion, explicit
   digit-count, length, sign and overflow constraints.
2. Closed interval relations, including boundary touch, exact order
   reversal and positive scaling on a clearly supported domain.
3. Missingness as a distinct type: absent, measured or processed,
   evaluated boundary zero, and invalid value.
4. Original acquisition/source identity separation, including
   measurement hashes, diagnostic hashes, diagnostic event IDs,
   lab families and TRAIN/HOLDOUT roles.

Pin versions of GNAT, GNATprove, SMT solvers, source commit and all
proof assumptions. Actually execute GNATprove and save all failures,
proof results and accepted assumptions. Independently execute
Ada and stdlib Python differential vectors on valid, invalid, edge,
overflow and missingness cases. Separate proved numerical properties
from finite implementation tests and from scientific interpretation.

Use offline tools and uv run --no-project for Python, avoiding
Docker/Kubernetes/NPM/cloud infrastructure unless explicitly needed.

**Current status:** NOT_STARTED, no GNATprove proof asserted by 010.

## Phase B — VANILLAJS Lean-to-ECMAScript refinement

The separate unresolved obligation is in QSOLKCB/VANILLAJS,
docs/Q16_FORMAL_001.md, labelled REFINEMENT_OPEN. The Q16-FORMAL-002
historical original and recovery evidence remain immutable and
must not be relabelled as a universal production JavaScript proof.

A dedicated PR should pin the actual production
modules/integer-math/index.js and relevant vector source blobs,
Lean toolchain and ECMA-262 version. Model ECMAScript IEEE-754
Number, ToInt32/ToUint32, truncation versus floor, NaN,
infinities, negative zero, bounds, exceptions, loops, overflow
and typed arrays for an explicitly declared input domain.

Prove the scoped refinement with an axiom audit, or provide
an executed counterexample and corrected implementation. Independently
run source-pinned conformance and adversarial differential tests.
Finite JS tests do not prove universal equivalence; a Lean integer
theorem does not establish software authorship or code provenance.

**Current status:** REFINEMENT_OPEN, not executed in MAT-SPEC-010.

## Scientific continuation outside numbered profiles

The independent physical helium phase study remains blocked:
source-separated original measurements with per-row calibrated
errors and orthogonal phase diagnoses are not yet admitted.
Any future genuine experiment is an additional separately approved
research programme, not a revision of prior results.
