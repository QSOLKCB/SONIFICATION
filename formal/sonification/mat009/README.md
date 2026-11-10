# MAT-009 scoped formal verification

The frozen production subject is `mat-spec-009-v0.1.0`, commit
`0758a96360726aafbb07abed34620eda178407ae`. The source binder checks
that release and its direct MAT-008 parent against recorded Git bytes and
selected Python syntax. It does not prove source semantics.

## Verified scope

- The Lean 4.19.0 model proves eligible-row split membership, sticky conflict,
  final intersection and parent reason union. A separate model proves the
  validated diagnostic registry's first-owner behavior. There are 22 named
  intended theorems; the full proof-module inventory has 351 declarations,
  including 95 theorems and 146 compiler auxiliaries.
- Exact built-in finite conformance covers 4,096 four-row role, campaign and
  lab combinations, plus named cases. The retained full repository run passed
  329 tests and 202 subtests before the audit repair. The focused post-repair
  receipt suite passed 15 tests.
- The first independent audit **failed** with `MAT009-AUDIT-001`: a user axiom
  and theorem of `False` ending `_cstage1` escaped the standalone Lean audit.
  That report and its logs remain at `audit/report.json`.
- The repaired gate rejects that exact mutant and an independent `_cstage2`
  variation. Seven negative controls passed. The fresh independent audit of
  candidate `b07942c77bebb15c99d8a70f52397d4077694ea0` reports **PASS for
  this scoped mathematical audit gate** in `audit/repair-audit-001/report.json`.

The audit checks every declaration from the five proof modules. Safe
declarations may depend only on `propext`, `Quot.sound` and
`Classical.choice`. Two exact unsafe compiler axioms and the `lcProof` and
`lcUnreachable` compiler mechanisms are disclosed in `lean/PROOF_NOTES.md`.
Their use is confined to unsafe compiler auxiliaries. The pinned Lean binary
and 1,303 hashed toolchain imports remain trusted inputs.

## Open obligations

`REFINEMENT_PROVED` remains **OPEN** for the MAT-009 child and direct MAT-008
parent. The model omits skipped/raw Python records, other child reasons,
several diagnostic outcomes, exceptions and observable status. Neither these
proofs nor finite tests authenticate physical evidence, independence or
classifier accuracy. The general `MAT009.partition` target in
`../theorem-map.json` remains OPEN; only its three scoped partial rows have
positive results. Future proof-source rebaselines need renewed review because
absence of a source declaration range alone is not universal compiler
provenance.

## Local verification

From the repository root, with the pinned Lean toolchain installed:

```sh
python3 formal/sonification/mat009/source/source_bind.py
python3 formal/sonification/mat009/verify_evidence.py
python3 formal/sonification/mat009/lean/verify.py
python3 formal/sonification/mat009/lean/verify_negative.py
python3 formal/sonification/mat009/lean/verify_repair.py
python3 -m pytest -q tests/test_sonification_formal_mat009_lean_receipts.py tests/test_sonification_formal_mat009_negative_receipts.py tests/test_sonification_formal_mat009_suffix_axiom.py
```

`lean/attempts/002`, its six negative controls, the failed audit, and the
original checkpoint remain immutable research evidence. New executions use
separate directories.
