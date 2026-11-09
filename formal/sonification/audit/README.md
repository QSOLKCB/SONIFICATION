# Independent adversarial audit

`attempt-003/AUDIT.json` is the accepted local audit for the exact input hashes
listed there. The auditor inspected the actual production source pin, proof
modules, typed statement consumers, axiom scanner and runtime adapter, then
executed the checker and mutations independently in temporary copies.

All 19 named model statements passed independent replay. They cover integer
closed intervals and a separately stated abstract order contract. The generic
order contract's laws are explicit hypotheses. The integer instantiation and
inhabited-branch theorem establish a nonempty supported model. Positive scaling
requires a strictly positive integer. The interval construction theorem accepts
nonnegative integer error; production parsing instead requires strictly positive
reported decimal error. This distinction is retained, not inferred away.

Typed consumers rejected a same-name theorem weakened to `True`. Other controls
rejected a false theorem, a `sorry` hidden in a data-valued helper under an
unrelated namespace, a custom axiom, a broken unimported nested module, a missing
import, a counterfeit empty zero-exit prover report and missing expected
inventory. Independent source-byte and numerical-result mutations were detected.

The axiom scan examines all 217 originating project declarations, including
generated helpers and Audit consumers. Safe declarations admit only `propext`,
`Quot.sound` and `Classical.choice`, as reported per declaration. Unsafe compiler
auxiliaries are separately disclosed and may additionally use Lean's `lcProof`
and `lcUnreachable`; those never appear as safe theorem dependencies in this
audit. The Lean kernel, pinned distribution and its imported module hashes,
audit metaprogram, Python, Git, operating system and hashing remain trusted.
Distribution origin was not independently authenticated.

The 50,630-case classification corpus and 26 unit tests passed on the recorded
CPython runtime. These tests establish finite conformance only. Production
Python refinement, arbitrary Fraction correspondence, rational instantiation of
the order contract, full callers/dependencies and the complete mission remain
OPEN. Owner review of the intended scientific specification remains pending.

Attempt 001 completed successfully before audit-runner provenance was added.
Attempt 002 failed while constructing its final report because of an auditor
runner `NameError`; its inputs and command outputs remain preserved and it grants
no audit acceptance. Attempt 003 corrected that runner defect and completed.

Reproduce from repository root, with the pinned Lean binary available:

```sh
python3 formal/sonification/audit/run.py --out /tmp/sonification-new-independent-audit
```

Use a new output directory. This run never modifies frozen production sources,
tags, datasets or historical proof receipts. Review new input hashes before
reusing any prior acceptance.
