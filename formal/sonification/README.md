# SONIFICATION-FORMAL-001

This is an incremental investigation of frozen SONIFICATION implementations.
The project is INCOMPLETE. Source enumeration, mathematical proofs,
implementation refinement and runtime conformance have separate statuses.

Start with PROOF_INVENTORY.md, SOURCE_MANIFEST.json, theorem-map.json and
CLAIM_BOUNDARIES.md. The machine implementation inventory identifies historical
operations; OPEN entries are requirements, never implied proof coverage.

Review stages:

- PR A: historical identities, inventory, claim boundaries and infrastructure.
- PR B: initial Lean model proofs, typed statement consumers, complete module
  and axiom audit, preserved attempts and negative mutation controls.
- PR C: source-sensitive Python refinement investigation and independent
  conformance tests; retain OPEN wherever semantic correspondence is unproved.
- Later increments: MAT-SPEC-008–010 admission, provenance and archive gates;
  MAT-SPEC-001–006; D4-TIA; ETQ; remaining dependencies and operations.

Use Python standard library commands from the repository root. Each stage's
receipt identifies actual argv, working directory, tool bytes and version,
input hashes, expected/observed obligations and original stdout/stderr.
No result is accepted merely because a process exits zero.

Historical releases and proof receipts are read-only inputs. The private
protocol workspace is deliberately outside the public repository. Its
bootstrap, contract loading, manifest verification, `init`, `validate`,
`bundle`, `next` and environment probes are recorded there.

Resume by checking the current branch against the recorded candidate SHA,
revalidating historical identities and following HANDOFF.json. Never rewrite
an old attempt to make a later attempt appear successful.
