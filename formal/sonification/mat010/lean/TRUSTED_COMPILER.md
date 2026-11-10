# MAT010 Lean compiler trust boundary

The pinned Lean 4.19.0 build of the final Phase A `ArchiveModel.lean` and
`ArchiveConsumer.lean` reports 333 project declarations: 63 theorem
declarations, 151 compiler auxiliaries, including 15 unsafe compiler axioms
and 136 unsafe definitions. Every one of these auxiliaries lacks a source
range. The model and typed consumer contain no source-level `axiom`, `unsafe`,
`sorry`, `admit`, `opaque`, `partial`, macro, elaborator, or `run_cmd` command.

`LeanAudit.lean` enumerates all project declarations by module origin. It
rejects every source-level project axiom, including compiler-looking suffixes,
and rejects unknown unsafe compiler axioms. The Python checker pins the exact
full declaration inventory, including name, type, source-range status, unsafe
status, and transitive axioms. Thus an additional generated-looking unsafe
definition cannot be accepted merely by its spelling. The two controls with
source axioms named `_cstage1` and `_cstage2` must both fail.

The 15 explicitly trusted project compiler axioms are Lean specializations of
`List.flatMapTR.go`, `List.foldl`, `List.hasDecEq`, `List.isPrefixOf`,
`List.isSuffixOf`, and `List.mapTR.loop` for this exact source and binary. Their
full names and observed types are retained in `compiler-trust.json` in the
accepted proof receipt. Their own types do not assert scientific or logical
model propositions; they are confined to unsafe compiler auxiliaries. The
ordinary named A1–A7 theorems depend only on `propext` and `Quot.sound`.

Three imported compiler axioms can appear in those unsafe auxiliaries:

- `List.elem._at.System.FilePath.normalize._spec_1`
- `_private.Init.Data.Option.Basic.0.Option.decEqOption.«_@».Init.Data.Option.Basic._hyg.4._at.Std.Time.Database.TZdb.idFromPath._spec_1`
- `lcProof`

The accepted receipt records the SHA-256 identities of all imported toolchain
modules and the Lean executable. These compiler axioms are not allowed in
ordinary project definitions or theorems. Logical dependencies permit only
`propext`, `Quot.sound`, and `Classical.choice`; `sorryAx` and other project
axioms are prohibited.

This is a trust audit of kernel propositions and generated compiler artifacts,
not a proof that the Lean compiler or machine executable is free of defects.
