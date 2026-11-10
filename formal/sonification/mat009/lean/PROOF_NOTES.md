# MAT009 split-model proof notes

`SplitModel.lean` models only rows that have passed the child campaign, role,
and lab guards. Parent reason IDs are an arbitrary input set. `step` updates
the latest campaign owner and persistent membership sets. `finalize` performs
the campaign/lab set intersection after the full scan. `DiagnosticFirstOwner.lean`
separately models one validated diagnostic identity registry's `setdefault`
behavior. These are mathematical models, not a refinement proof for the frozen
Python source or CPython execution.

## Failed attempts retained

- The first direct `lean SplitModel.lean` pass left goals in R2 (a nonmatching
  key needed an introduced `key ≠ row.campaign` hypothesis), R4 (set/reason
  stickiness needed explicit `Or.inl`), and the scan membership proofs (the
  existential over `row :: rest` needed an explicit head/tail equivalence).
  All were discharged in the compiled file.
- `prefix` was rejected as a Lean keyword in the finite-scan theorem. The
  binders are now `before` and `after`.
- The first diagnostic registry compile left the `key = identity` branch
  unresolved in `register_preserves_existing`. Substituting the key before
  simplification discharged it.

## Counterexamples preserved in Lean

- `overwrite_retains_both_split_memberships`: after TRAIN then HOLDOUT for the
  same campaign, its latest owner is HOLDOUT while both historical campaign
  memberships remain. A final-owner-only leakage test would miss this case.
- `parent_can_supply_leakage_reason`: a parent can supply the leakage reason
  ID while the child has no campaign/lab intersection. The final union and
  child intersection are distinct predicates.
- `Diagnostic.first_owner_not_last_writer`: a later different diagnostic
  claimant does not overwrite the first owner.

## Open boundary

The child eligibility guards, other child checks (phases, receipts, units,
pressure, scale, labels, diagnostic validity), MAT008's implementation,
source-to-model correspondence, and CPython refinement are outside these
theorems. `STRUCTURAL_ONLY_UNAUTHENTICATED` is represented only as a status;
no physical evidence or independence is authenticated.
