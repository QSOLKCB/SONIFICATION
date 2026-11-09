# Independent mathematical proof audit

`attempt-004-model/AUDIT.json` records an independent replay of the exact
mathematical proof inputs and eight adversarial controls. This audit is usable
with PR B alone: it imports no Python refinement adapter, executes no differential
corpus, and does not depend on artifacts introduced by a later PR.

The auditor inspected the actual Lean definitions, independently typed consumers,
origin-module declaration scanner and frozen production source locator. The
production locator provides traceability only; no source-refinement relationship
is asserted. The frozen MAT-SPEC-007 tag object, peeled commit and complete source
module SHA-256 were checked directly with Git and the production bytes retained.

All 19 intended mathematical theorem statements passed. They concern integer
closed intervals and an explicitly assumed abstract strict-order contract. The
integer instance and inhabited-branch theorem rule out an entirely empty model.
Positive scaling requires a positive integer. The construction theorem assumes
nonnegative integer error; production parsing has a separate strictly positive
decimal-error condition. Rational instantiation and Python correspondence remain
OPEN.

All eight controls were rejected: false theorem, same-name weaker theorem,
`sorry` in a data-valued helper under an unrelated namespace, custom axiom,
unimported nested module, missing import, empty zero-exit counterfeit prover and
missing expected declaration inventory. Each control ran in an isolated copy;
mutated inputs and original streams are preserved.

All 217 originating project declarations were examined, including generated
helpers and statement consumers. Safe declarations use only the disclosed
logical axiom set `propext`, `Quot.sound` and `Classical.choice`. Unsafe compiler
auxiliaries may additionally use `lcProof` and `lcUnreachable`; the audited safe
theorem dependencies do not. Trust includes Lean 4.19.0's kernel and pinned
distribution/imported module bytes, audit metaprogram, Python, Git, operating
system and SHA-256. Distribution origin is not independently authenticated.

The four dimensions remain independent: MODEL_PROVED and AUDIT_ACCEPTED are PASS
only for the exact linked model statements; REFINEMENT_PROVED is OPEN and
DIFFERENTIAL_TESTED is NOT_EXECUTED in this receipt. No scientific result is
established. Owner review of the intended scientific specification is pending.

From the repository root, with the recorded Lean binary installed, reproduce:

```sh
python3 formal/sonification/audit/model_run.py --out /tmp/sonification-new-model-audit
python3 formal/sonification/audit/model_verify.py
```

The first command requires a new output directory; the second validates the
retained attempt-004-model receipt against current audited input bytes. Existing
attempts remain append-only. A later combined conformance audit is separate.
