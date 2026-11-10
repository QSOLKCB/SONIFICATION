# After MAT-SPEC-010 — Formal verification handoff

**The numbered MAT-SPEC series closes at 010.**
Future work is a separate verification programme, not MAT-SPEC-011,
and cannot retrospectively promote an earlier blocked scientific gate.

## Phase A — SONIFICATION SPARK/Ada proof (executed separately)

The separate GNATprove pilot and follow-ups were subsequently
executed with source-pinned receipts. The planned contract below
is retained as a historical design specification.

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

**Current status:** separate SPARK-001 v1.0.0 (26/26),
SPARK-002 Phase 1A (23/23) and Phase 1B (9/9) have executed
owner-pinned GNATprove receipts. The historical MAT-SPEC-010
profile itself asserts none of these proofs.

## Phase B — VANILLAJS Q16 corrective work (completed separately)

The original follow-up has been delivered in VANILLAJS:
Q16-FORMAL-001, sealed Q16-FORMAL-002 evidence, and merged
[Q16-ECMA-001 PR #60](https://github.com/QSOLKCB/VANILLAJS/pull/60).
The latter checks bounded integer projections in Lean and executes
source-pinned JavaScript conformance with negative counterexamples.
It is incorrect to schedule the corrective milestone as not started.

**Boundary:** universal Lean-to-production ECMAScript refinement
remains `REFINEMENT_OPEN` inside VANILLAJS. Neither the integer
theorems nor finite JavaScript tests establish all IEEE-754 Number,
coercion, loop, exception, or engine semantics. Future universal
proof work requires separate scope and authorization; it is not
a MAT-SPEC-010 completion condition. Historical seals remain intact.

## Scientific continuation outside numbered profiles

The independent physical helium phase study remains blocked:
source-separated original measurements with per-row calibrated
errors and orthogonal phase diagnoses are not yet admitted.
Any future genuine experiment is an additional separately approved
research programme, not a revision of prior results.
