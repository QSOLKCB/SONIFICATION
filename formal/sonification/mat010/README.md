# MAT-010-CLOSURE-001

This directory contains scoped formal and execution evidence for frozen
MAT-SPEC-010. The first review scope is direct archive-membership validation
(`validate_archive_membership`, Phase A). Parent integrity and scientific
closure remain separately tracked obligations until their own proofs and audit
are complete.

`SOURCE_BINDING.json` pins the annotated release, peeled commit, source tree,
module blob, module SHA-256, predecessor commit, and exact AST spans. Run
`python3 -m formal.sonification.mat010.source_bind` to recheck those identities.

`conformance.py` executes a local synthetic finite corpus against the frozen
Python function. It reports expected and actual results, including deliberate
boundary counterexamples. `receipts/source-001`, `receipts/finite-001`,
`receipts/proof-001`, `receipts/proof-002`, and the two negative-control runs
retain original streams and SHA-256 manifests. `negative-001` is a preserved
failed expectation; `negative-002` passed all six controls. Run
`python3 -m formal.sonification.mat010.verify_evidence` to verify every retained
receipt and all development attempts. The verifier pins each original input
commit rather than replacing historical runs when verification code changes.

The Lean model and declaration gate are in `lean/`. Every development attempt
is retained in numbered, append-only subdirectories. `proof-002` is the latest
nominal accepted local proof receipt; independent audit is still pending. The
mathematical proof scope, Python conformance scope, and scientific limits are
listed in [CLAIM_BOUNDARIES.md](CLAIM_BOUNDARIES.md).
