# MAT-SPEC-008 run ownership mathematical model

`Sonification.Mat008.reused_run_blocks` proves that any two rows in any finite
list with equal original run identifiers and unequal campaign identifiers force
the final model's conflict flag to `true`. The theorem has no input-size bounds
and no assumptions about distinct row positions or the order of the witnesses.
All strings are allowed mathematically; Python identity parsing is outside this
model. The exact universal proposition has a fixed typed consumer in `Audit.lean`.

`ParsedRow` is independently authored and contains only `campaign` and
`originalRun`. The owner map is represented by an association list: lookup uses
the first matching key, so pushing a new pair implements latest-owner lookup.
`scanFrom` recursively processes the finite list. Each step ORs a newly detected
owner mismatch with the prior conflict flag. `scan_clear_covers` establishes the
critical history invariant: without a conflict, every previously processed row
agrees with the final owner of its run. Two disagreeing witnesses contradict
that invariant. `nonvacuity` checks a collision followed by an independent row
and a separate collision-free example.

This is a mathematical model result. Python implementation refinement remains
OPEN. Required bridges include identity parsing and rejected-row projection,
mutable dictionary and set semantics, short-circuit evaluation, exceptions,
control flow and final status/output correspondence. This model does not
establish complete MAT-SPEC-008 eligibility, primary source authenticity,
physical independence, phase classification accuracy or empirical admission.

The production reference is the frozen `mat-spec-008-v0.1.0` peeled commit
`b4247877dd471e2e9d4986c86bdc1f11b14e43f8`, implementation file SHA-256
`e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08`.
No production source or historical artifact is copied or modified here.

Run with the actual Lean 4.19.0 executable and a new output directory:

```sh
python3 formal/sonification/mat008/lean/check.py \
  --lean /path/to/lean-4.19.0/bin/lean \
  --out /tmp/mat008-new-proof \
  --baseline-commit FULL_REVIEWABLE_INPUT_COMMIT
python3 formal/sonification/mat008/lean/negative.py \
  --lean /path/to/lean-4.19.0/bin/lean \
  --out /tmp/mat008-new-negative
```

A development run may omit `--baseline-commit`; it does not have an independently
reviewed input baseline. The designated Git baseline checks input identities
against immutable Git objects. Original logs are append-only. The checker
compiles all three active modules separately in a fresh directory and requires
exactly 99 originating declarations and 10 named model/support theorems. It
collects all transitive axioms, including safe data helpers, generated results,
compiler auxiliaries and Audit consumers, before classifying declarations.

All final declarations use only `propext`, `Quot.sound` and `Classical.choice`;
there are no project axioms, `sorryAx`, `lcProof` or `lcUnreachable` dependencies.
Lean 4.19.0 kernel/distribution, the audit metaprogram/runner, OS execution and
installed binary provenance remain trusted. The successful runner records
actual executable SHA-256 and imported toolchain `.olean` digests. It does not
prove its own correctness or authenticate external execution.

The negative runner requires the intended error class for each mutation. It
removes sticky accumulation, weakens the main theorem under the same name,
introduces a data-valued `sorry` helper and adds an unimported module. The sticky
mutation has a separate kernel-checked counterexample proving that its A/B
collision is erased by a later independent row. Negative receipts concern model
and audit detection only; they are not Python refinement proofs.

`attempts/` preserves failed elaborations, obsolete representations, trust-audit
diagnostics and complete fresh runs. These archived `.lean` snapshots are
excluded from the active module set. Attempt 016's original aggregate was
explicitly invalidated because incomplete mutant fixtures caused rejection at
the wrong gate; its logs remain intact. An exclusion or an unrecorded failure is
never treated as proof completion.
