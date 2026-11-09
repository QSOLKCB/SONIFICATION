# First model-proof result

The frozen production reference for this slice is MAT-SPEC-007 tag object
`8b933a5ab09b8e76afe4c8e169e089f251e23314`, peeled source commit
`b97348ff8fcf3f57764dec21a8914f153f96a745`, tree
`c1b842c6bace3ccb01714007b8d7ebb05bcecd31`, and
`materials/mat_spec_007.py` SHA-256
`2e363adea6c781ab68aec69d2ee5c7d712fc5e46346ae5be21d8cf3e929781c6`.

The mathematical model is defined in `lean/Sonification/Intervals.lean` and
`lean/Sonification/OrderedIntervals.lean`. Nineteen named theorems compiled
under Lean 4.19.0. Their exact types and transitive axiom lists are in
`lean/theorem-statements.json`; typed consumers in `lean/Audit.lean` require
the intended propositions. The fresh replay at
`lean/attempts/root-replay-001/result.json` records 19 expected and 19 observed
theorems, 217 origin-module declarations, executable identity, imported
toolchain hashes, command lines, return codes and original logs.

The integer model proves invalid-interval rejection, exhaustive and exclusive
closed interval classification, reversal, touching overlap, positive integer
scaling and the validity of a box with nonnegative integer error. The generic
order model proves the declared conditional comparison laws and an
order-reflecting map result. Its assumptions are explicit structure fields;
an integer instance and branch examples witness satisfiability. No rational
or `fractions.Fraction` instance is supplied.

The private protocol records the model, source and evidence as separate
dimensions. These public artifacts contain no private protocol templates.
The mathematical proof rests on the Lean kernel and bundled libraries.
Reported logical dependencies are `propext`, `Quot.sound` and
`Classical.choice`. Unsafe compiler-generated LCNF auxiliaries separately
use `lcProof` or `lcUnreachable`; no safe theorem or helper depends on them.
The audit treats the compiler, elaborator, audit script and installed binary
as trusted software and records their identities. Early failed attempts and
an invalid auditor-runner attempt are retained with their limits.

The independent audit result is `audit/attempt-004-model/AUDIT.json`, with
its source/log binding checked by `audit/model_verify.py`. All eight deliberate
proof/evidence mutations were rejected. The audit accepted the 19 exact
mathematical statements under their declared assumptions. It must be rerun or revalidated for any changed proof input. Owner
review of the intended specification is still pending. A zero process exit
alone is not accepted evidence.

The production `classify`, `interval` and `pairwise_fits` obligations remain
OPEN. In particular, integer endpoints and `Option.none` do not establish
CPython `Fraction` comparison or `ValueError` behavior. The first Python
investigation and finite conformance results belong to the next stage.

The next proof obligation is a checked rational-order instance with exact
numerator/denominator semantics, followed by a source-sensitive Python
operational semantics and a proved representation/observable-output bridge.
MAT-SPEC-008–010 admission and provenance, earlier MAT-SPEC stages, D4-TIA and
ETQ remain in the historical inventory with OPEN assurance dimensions.
