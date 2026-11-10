# MAT-010 assurance boundaries

Frozen source: annotated `mat-spec-010-v0.1.0`, commit
`9d12c6a5098f4edba972bb6b1067555d8f48f693`, module SHA-256
`e062474d4435e769f8c6c8407bc44ad89cfb2dfa04677b820c3a035d604a9056`.
`SOURCE_BINDING.json` and `source_bind.py` bind bytes and AST spans. They do not
establish CPython semantics or the authenticity of external physical data.

| Target | MODEL_PROVED | REFINEMENT_PROVED | DIFFERENTIAL_TESTED | AUDIT_ACCEPTED |
| --- | --- | --- | --- | --- |
| Archive membership, Phase A | PASS for scoped finite-list model at proof-002 | OPEN | PASS for declared exact built-in finite cases | PENDING independent audit |
| Parent integrity, Phase B | OPEN | OPEN | NOT_EXECUTED | OPEN |
| Scientific closure, Phase C | OPEN | OPEN | NOT_EXECUTED | OPEN |

## Archive validator

The direct frozen validator requires nine ordered profile/snapshot identifiers,
unique merged-commit values, matching versions, nonempty member dictionaries,
the declared evidence-file key in each map, syntactic commit/name/digest checks,
stage-001-only MIDI, unique output logical paths, and a final stage-009 artifact.
It sorts each stage's declared member entries. It does **not** require each
directly supplied artifact map to equal a fixed exhaustive ancestor inventory.
The actual frozen caller supplies the specific imported predecessor maps; the
direct validator also accepts additional well-formed names and omission of
non-evidence names. The finite corpus records these accepted cases rather than
reclassifying them as rejection.

The pure Lean model covers exact string and finite map representations under
its stated definitions. The finite Python corpus contains 28 cases, including
23 exact built-in cases matching their declared expectations. Three adversarial
subclass cases are counterexamples to extending that model contract to arbitrary
Python subclasses: duplicate textual commit identity, hidden evidence during
`items()` iteration, and an overridden `.endswith()` MIDI check. Direct malformed
inputs may raise incidental exceptions. These observations do not prove
arbitrary-input CPython refinement.

The accepted Phase A Lean receipt is `receipts/proof-002`, bound to proof-input
commit `2f2ea6d3deffebc7a552ec79f42ea829b9812d3e`. It records the seven
typed A1–A7 statements, 333 project declarations, complete transitive axiom
results, and 1,303 hashed external toolchain imports. `negative-002` rejects
six controls, including both compiler-suffix `False` axioms. The first negative
run remains `FAIL`: it expected a `sorry` rejection at compilation, while the
actual transitive axiom audit rejected `sorryAx`; this expectation was corrected
without changing the gate. These are nominal and adversarial local results;
independent audit is a separate dimension.

## Parent and closure

The frozen parent verifier compares the exact seven-key predecessor set with
trusted expected digests and checks selected parsed manifest, split, audit, and
gate fields. It does not individually check `gate.physical_evidence_admitted`.
The closure function does check that field, plus null classifier accuracy in
split and audit. The closure copies several input fields without validating
their values inside that function. Any model theorem about fixed returned
closure fields therefore depends on its stated successful-return premise;
stronger claims need explicit caller or parent premises.

SHA-256 syntax, computed hashes, trusted expected hash values, Git source
identity, and physical source authentication are separate claims. No software
proof removes collision risk, proves archive deposition, or establishes new
experimental physics.

## Scientific status

Independent experimental replication: `NOT_DEMONSTRATED`. Real classifier
training: `False`. Real held-out accuracy: `null`. Human auditory test:
`NOT_PERFORMED`. New critical exponent: `NOT_FITTED`. E8 or unification:
`NOT_CLAIMED`. MAT-SPEC-011: not allowed by the frozen closure record.
