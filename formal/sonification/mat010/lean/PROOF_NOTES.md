# MAT010 Phase A archive model

`ArchiveModel.lean` models the accepted path of frozen
`materials/mat_spec_010.py::validate_archive_membership` (annotated
`mat-spec-010-v0.1.0`, peeled commit `9d12c6a5098f4edba972bb6b1067555d8f48f693`,
lines 225–274). It is an independently specified mathematical model over
arbitrary finite claim and snapshot lists. There is no fixed bound on member
counts. `ArchiveConsumer.lean` imports the model and checks the exact types of
all seven public theorems.

The model's input domain has exact string fields and a list of members per
snapshot. Successful validation requires distinct member names, representing
the unique keys of a built-in Python dictionary. It does not model dict or
string subclasses, mutation, Python exception order, bytes, SHA-256
computation, Git identity, filesystem operations, or `Path.suffix` execution.
Pure character-list functions describe the accepted basename suffixes, MIDI
suffix, and stage-number extraction; their correspondence to CPython remains
a separate obligation. `Artifact.name` is a model-only source-key witness
absent from the Python output record.

The model checks nine ordered claim and snapshot stage IDs, distinct
syntactically valid 40-character commit strings, matching versions, nonempty
member maps, each claim's evidence member, distinct member names, syntactically
valid names and 64-character digests, the stage-001 MIDI restriction, unique
constructed logical paths, and the final emitted stage. It sorts names within
each stage. It does **not** require exact pinned member maps: additional
well-formed members and omission of non-evidence members are permitted when
the other guards still hold. The fixed 63-member caller result is not a
theorem of the direct validator.

| Theorem | Mathematical result for any successful finite input |
| --- | --- |
| `M010_A1_ordered_nine` | Both stage sequences equal the nine constants; both lists have length nine. |
| `M010_A2_commit_identities` | Claim commit strings are distinct and pass the lowercase-hex, length-40 check. |
| `M010_A3_valid_artifact_identity` | Every emitted artifact has a stage in the nine constants, a valid name and digest, the stage-001 MIDI restriction, and a source member in a paired claim/snapshot whose version equals the artifact version. |
| `M010_A4_unique_logical_paths` | Emitted logical paths are distinct, and the final artifact has stage 009. |
| `M010_A5_deterministic_enumeration` | For corresponding snapshots with equal ID/version and permuted complete `(name, digest)` members, assuming distinct member names, the entire ordered `emit` and `validate` outputs are equal. Per-stage sorting is a proved helper. |
| `M010_A6_fail_closed_malformed` | `validate = none` for any of 13 explicit malformed classes: wrong claim/snapshot stage order, repeated/bad commit, version mismatch, empty members, missing evidence member, repeated member name, bad name, bad digest, forbidden MIDI, repeated logical path, or wrong final stage. |
| `M010_A7_accepted_and_rejected_nonvacuity` | Concrete nine-stage single-evidence and extra-member inputs succeed; an empty snapshot list is rejected. The base input omits the extra non-evidence member, showing exact-map coverage is not imposed. |

The `audioRendered = false` result is a record label, not proof about external
runtime audio. Digest syntax does not verify the referenced bytes. No theorem
here proves source-to-model or CPython refinement, transitive MAT009 replay,
archive deposition, or scientific evidence admission.

## Development compiles

Each `development/NNN` directory is append-only and contains the exact source
snapshot, toolchain file, command list, stdout/stderr, and exit status for each
attempted command. `001`–`002` record initial elaboration failures; `003`
compiled an earlier, weaker theorem map. `004`–`015` retain the revision and
failed witness-reduction attempts, with successful model-only compiles at
`005` and `016`. `017` compiled the final model and typed consumer with Lean
4.19.0, exit 0/0. The final consumer's `#print axioms` output reports only
`propext` and `Quot.sound` for each of A1–A7. The accepted witness uses
ordinary kernel-checked simplification and `decide`; it does not use
`native_decide`. No final accepted receipt is created here; proof inputs must
first be committed and independently audited.
