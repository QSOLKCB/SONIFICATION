# Abstract ownership-state correspondence

These Lean proofs establish a correspondence between two **mathematical
models**. They do not establish that the frozen MAT-SPEC-008 Python implementation
implements either model. `REFINEMENT_PROVED` remains `OPEN`.

The production source being investigated is `materials/mat_spec_008.py` at
`b4247877dd471e2e9d4986c86bdc1f11b14e43f8`, SHA-256
`e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08`.
This subtree neither imports nor executes that source. A separate source binder
and its semantic assumptions must supply the missing connection.

## Models and relation

`Refine/MapReason.lean` independently defines a functional ownership map
`String → Option String`, a reason-set characteristic function `String → Bool`,
and accepted rows containing a campaign and an original-run string. The naming
`AbstractPy`/`PyState` identifies the intended abstraction target; it does not
claim a formal semantics of Python.

`pyStep` first looks up the old campaign for a run. An existing, different
campaign inserts `REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS` into the reason set. It
then overwrites the owner with the current campaign. The models preserve other
reason memberships. A missing owner is distinct from every stored string.

The accepted mathematical model is `Mat008.RunOwnership`, frozen at main commit
`ac1408cf0c459d79c3d0552287812a15ce644f0d`, with source SHA-256
`653f4638568e4e461176cca7659360737f3ac2632152163602c789fd65ead201`.
The checker verifies those bytes and compiles a temporary copy; the accepted
file and its existing receipts are unchanged.

`Related s m` means:

```text
(∀ key, s.owners key = Mat008.lookup m.owner key)
∧ s.reasons reuseReason = m.conflict
```

Thus association lists with shadowed historical entries represent functional
overwrites by first-match lookup. `r2_finite_support` proves that any ownership
map related to the finite association list has finite support. Arbitrary
unrelated maps are not assumed finite.

`runGateProgram` provides a small independent instruction semantics for the
source binder to target: `testExistingOwner` (0),
`insertReasonIfMismatch` (1), then `overwriteOwner` (2). For every state, row and
arbitrary initial mismatch flag, `instruction_program_correspondence` proves
that this sequence has the same resulting state as `pyStep`. The test resets
the flag before it is used. Other instruction numbers are no-ops. A theorem
about this instruction program does not verify its extraction from Python.

All semantic definitions are explicitly `noncomputable`: their logical bodies
remain available for kernel reduction, without asserting a compiled runtime
dictionary implementation. Failed attempts with compiled specializations are
retained rather than exempting their axioms from the audit.

## Executed R1–R7 statements

All row and state variables below are universally quantified. The exact Lean
types, including every quantifier and per-theorem axiom list, are pinned in
`theorem-statements.json` and checked by fixed typed consumers in `Audit.lean`.

| Requirement | Executed mathematical theorem and premises |
| --- | --- |
| R1 | `r1_empty_related`: `Related empty initial`. The abstract map is everywhere `none` and the abstract reason set everywhere `false`. |
| R2 | `r2_lookup`: `Related s m → ∀ key, s.owners key = lookup m.owner key`. This is a consequence of the explicitly assumed representation relation; it does not prove built-in Python string/dictionary behavior. `r2_finite_support` derives finite map support from that relation. |
| R3 | `r3_overwrite`: `Related s m → OwnersRelated (pyStep s row).owners (step m (projectRow row)).owner`. `r3_latest_campaign` proves that the resulting lookup of the current run is `some row.campaign`, even when the run already has an owner. `step_related` also proves full post-step `Related`. |
| R4 | `r4_reason_iff`: `Related s m → ((pyStep s row).reasons reuseReason = true ↔ (step m (projectRow row)).conflict = true)`. Both sides include prior conflicts. The separate `new_reason_iff_mismatch` requires `s.reasons reuseReason = false` to identify a newly present reason with the current mismatch. |
| R5 | `r5_reason_sticky`: `s.reasons reuseReason = true → (pyStep s row).reasons reuseReason = true`. `r5_sequence_sticky` proves the corresponding result for every finite accepted-row sequence. |
| R6 | `r6_sequence_related`: `Related s m → Related (pyScanFrom s rows) (scanFrom m (project rows))`. `r6_accepted_projection` extends this to explicit mathematical accepted/skip events; it does not define raw-row parsing. |
| R7 | `r7_collision_reason`: for every finite `rows` and every `a b`, `a ∈ rows → b ∈ rows → a.originalRun = b.originalRun → a.campaign ≠ b.campaign → (pyScanFrom empty rows).reasons reuseReason = true`. It uses the accepted `reused_run_blocks` theorem through R6 and R1. |

There are 26 named theorems, including support lemmas and two counterexample or
nonvacuity statements; this count is not a count of Python-refinement results.
`nonvacuity` kernel-checks both a conflicting and a collision-free sequence.
`preexisting_reason_counterexample` shows why a prior-false premise cannot be
omitted from “reason present iff this row mismatches”: an already present reason
remains present even when the current row has no previous owner.

`acceptedProjection` removes `none` events. Here `none` means an explicit
mathematical skip with no observed state change, not an arbitrary Python row
that failed parsing. `skip_frame` permits changes to other reason memberships
provided all owner lookups and this reuse reason are unchanged. Proving that
each actual parsing/rejection path satisfies that frame remains open.

## Reproduction and trust audit

The pinned executable is Lean 4.19.0, commit `6caaee842e94`, Linux x86-64 release,
SHA-256 `92c3d35b5bfaa5e0fea413a775d504cf46cd95e1345df61c2274f76779e7e023`.
No network access or third-party Lean libraries are required. From repository
root, using previously unused output paths:

```sh
python3 formal/sonification/mat008/refinement/lean/check.py \
  --lean /home/trent/.elan/toolchains/leanprover--lean4---v4.19.0/bin/lean \
  --out /tmp/mat008-refine-fresh
python3 formal/sonification/mat008/refinement/lean/negative.py \
  --lean /home/trent/.elan/toolchains/leanprover--lean4---v4.19.0/bin/lean \
  --out /tmp/mat008-refine-negatives
```

After the inputs are committed, supply `--baseline-commit FULL_COMMIT_SHA` to
`check.py` to bind all proof/checker inputs to the reviewed Git object. The
development receipts deliberately record `baseline_commit: null`; they do not
pretend to provide that later commit binding. `check.py` is the authoritative
entrypoint: it supplies the externally pinned `Mat008.RunOwnership` source to a
fresh build and explicitly compiles all four modules. The minimal Lake file
alone does not supply that external dependency.

`Audit.lean` requires the four intended module origins (`Mat008.RunOwnership`,
`Refine.MapReason`, `Refine`, `Audit`) and inspects every declaration originating
there, including helper/data/generated declarations and typed consumers. It
rejects project axioms and every transitive axiom except `propext`, `Quot.sound`
and `Classical.choice`. Final execution audits exactly 253 declarations. No
`sorryAx`, `lcProof`, `lcUnreachable`, or project-specific assumption is allowed.
Declarations marked unsafe by the compiler are still inspected and their
observed axiom dependencies disclosed; this is not a proof of Lean's compiler.

The Python runner independently requires exact active module coverage, the
253-name inventory, all 26 intended names, their exact statements and observed
axiom inventories. It hashes the Lean executable, inputs, stdout/stderr and
imported toolchain `.olean` closure. The audit metaprogram, runner, operating
system execution, Lean kernel and pinned distribution remain trusted; the audit
does not prove itself correct.

`attempts/README.md` describes the retained development history. Final fresh
execution and negative-control receipts are identified in `HANDOFF.json`.
The seven negative controls independently reorder the gate, erase a sticky
reason, weaken R4, weaken R7, add a hidden non-propositional `sorry`, introduce
an unimported module, and change the accepted dependency bytes. Detection must
match the expected error and stage; an arbitrary failed command is insufficient.
The erasure mutation also has a separate kernel-checked counterexample.

## Open source obligations

No theorem here establishes a relationship to actual CPython execution. A full
bridge must establish at least the frozen-source control flow and extraction,
exact built-in string identity/equality and inequality, dictionary membership
and lookup, short-circuit safety, `None`/missing distinctions, set insertion,
owner overwrite, mutable aliasing/frame conditions, row-loop order, exception
behavior, accepted-row parsing/projection and final reason propagation. R2's
representation premise cannot serve as evidence that these obligations hold.
Other validator gates, packet eligibility, JSON/CSV behavior and scientific
claims are outside this slice.
