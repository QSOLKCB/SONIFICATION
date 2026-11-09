# Independent MAT-SPEC-008 audit

This audit accepts the ten explicitly recorded **mathematical model** theorems
and finite run-ownership observations. Python implementation refinement and the
remaining validator obligations are **OPEN**. There is no full-verification claim.

The proof inputs match commit
`c7889e3c9468ef4354d45d41b467263a0b5dea02` byte for byte. The tested checkout was
`c713b0c17f7b79b862e1581ac8aa166bf86935d2`. Production source is the immutable
MAT-SPEC-008 tag object `a02088e3c68addb41c9c7145694c0f566e84f87f`, peeled commit
`b4247877dd471e2e9d4986c86bdc1f11b14e43f8`, tree
`eb19f2e06a502442f621a73be1e5696c2fa25a65`. The production module SHA-256 is
`e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08`.

The canonical handoff is [attempt-001/AUDIT.json](attempt-001/AUDIT.json), SHA-256
`34eef078032bfb168faec6ba3bfe82cbf7e6bdc0412fe56820bc2bf2e26665d8`.
It records exact theorem types, per-claim assurance states, commands, original
stdout/stderr, input snapshots and 161 evidence-file hashes. Hashes bind content;
they do not authenticate an external experiment or constitute a digital signature.

| Assurance dimension | Result | Scope |
| --- | --- | --- |
| MODEL_PROVED | PASS | Ten exact Lean propositions; 99 observed declarations |
| REFINEMENT_PROVED | OPEN | No CPython-to-model correspondence theorem |
| DIFFERENTIAL_TESTED | PASS | Declared finite run-owner cases only |
| AUDIT_ACCEPTED | PASS | Exact mathematical and finite scope above |

`reused_run_blocks` quantifies over an arbitrary finite `List ParsedRow` and two
members. Equal original-run strings and different campaign strings imply that the
final model conflict flag is true. It has no row-count, eligibility, ordering or
distinctness precondition beyond the recorded membership/equality/inequality
hypotheses. The typed consumer preserves that proposition. Concrete collision and
noncollision examples are kernel checked, so the principal hypotheses are
satisfiable. The supporting `snoc_induction` type was also compared exactly.

A fresh direct Lean invocation built all three active modules in an isolated
directory. A separate fresh checker run agreed with the two supplied postcommit
receipts. All 99 declarations, including 22 unsafe generated compiler auxiliaries,
were scanned by origin module. Their transitive axioms are limited to `propext`,
`Quot.sound` and `Classical.choice`; no project axiom or `sorryAx` is accepted.
There is no compiler-axiom exception. The runner records 1,303 installed external
`.olean` identities. The Lean kernel, distribution, elaboration/audit metaprogram
and execution environment remain trusted components.

All four negative gates were rerun and their raw diagnostics inspected:

1. Removing sticky conflict propagation fails the model proof. A separate Lean
   counterexample confirms that this mutant clears an earlier collision.
2. Replacing `reused_run_blocks` with `True` fails its independently typed consumer.
3. A data-valued helper using `sorry` fails the transitive-axiom audit.
4. An additional unimported source module fails exact module coverage.

The submitted pairwise oracle and a separately authored grouping/set oracle both
checked 1,296 four-row assignments: 834 contain a run owned by multiple campaigns,
and 462 do not. Three targeted unit tests also passed. Source-byte drift and a
removed reuse reason were detected. Absence of run reuse does not imply complete
packet eligibility. These checks execute three exact frozen function bodies;
they do not execute full module initialization or prove Python semantics.

The independent counterexample uses `str` subclasses with equal text but different
hashes. `_identity` accepts them and the production dictionary gate omits the reuse
reason. A JSON round trip produces ordinary strings and restores blocking. The
finite domain is therefore explicitly limited to the recorded built-in values;
the unrestricted Python-object statement is false. The model theorem remains
valid. No production source was changed.

From the repository root, produce a fresh execution in a new, append-only directory:

```sh
python3 formal/sonification/mat008/audit/run.py attempt-NEW \
  --lean-root /absolute/path/to/lean-4.19.0
python3 formal/sonification/mat008/audit/verify.py attempt-001 \
  --lean-root /absolute/path/to/lean-4.19.0
```

The verifier deliberately accepts only the independently reviewed `attempt-001`.
A new execution remains raw evidence until a separate audit and reviewed digest
pin bind its receipt. The original verification command and streams remain under
`attempt-001/verification-001`; its original verifier source is preserved in
`attempt-001/inputs/audit-verify.py`.

`--lean-root` names the local installation directory containing `bin/lean` and
`lib/lean`. It can differ from the auditor's historical installation path.
The verifier retains those archived path strings as provenance, validates the
exact 1,303 imported module names and path layout, and hashes the local binary
and imported `.olean` files against the accepted digests. It does not read the
historical absolute paths. The selected installation must contain the exact
recorded Lean binary and imported library bytes, not just the same version
banner. The runner records failures and timeouts before returning a nonzero
exit status; its printed `status` and `execution-index.json` agree.

The hardened verifier pins the original `AUDIT.json` digest above, requires the
exact 161-file membership across this attempt and both postcommit Lean receipt
trees, and checks every recorded byte count and SHA-256. It rejects symlink
ancestors, roots, manifests and individual files; missing or extra evidence;
and extra empty directories. It compares accepted theorem rows against checker
declarations and validates all four per-claim assurance dimensions. Current proof
inputs must match the accepted snapshots. Optimized Python is rejected because
the retained semantic checks use assertions.

The append-only hardening receipt is
[binder-hardening-001/result.json](binder-hardening-001/result.json), SHA-256
`fd3c0391d4a7ca4f6fb6e7001e24a75f2659585351432a1ae0333fa7521ed463`.
Its verifier SHA-256 is
`2d12935d2d9eb1e5e4ee7b2f061771a9e426d1f52a6c07760bbc0a292dad5313`.
A valid isolated baseline passed. All 14 isolated mutations were rejected,
including weakened accepted claims, refinement promotion, missing logs, missing
one or all postcommit receipt trees, extra files or directories, symlinks,
jointly altered child evidence and manifest hashes, altered current theorem
metadata, and disabled assertions. The original accepted audit bytes remain
unchanged. Reproduce the controls with:

```sh
python3 formal/sonification/mat008/audit/binder_negative.py NEW_BINDER_ATTEMPT \
  --lean-root /absolute/path/to/lean-4.19.0
```

These are static evidence-integrity checks with trusted OS execution. They do
not prevent concurrent adversarial replacement, authenticate external sources,
or create new mathematical or Python-refinement evidence. The reviewed verifier
and independent digest pin remain trusted inputs.

The original hardening receipt above belongs to the prior verifier source and
is preserved unchanged. After the toolchain relocation fix,
[binder-hardening-002/result.json](binder-hardening-002/result.json), SHA-256
`664b11dee3da1b15aca4aead10e7c69963b13e845820ba68ae0d2d983b349656`,
replayed the baseline and all 14 negative cases against current `verify.py`
(SHA-256 `f682e110a1a66871ec1dedbaa448c98f0f6d16529589f2ff469b772bc5fd3e70`).

The relocation control at
[portability-002/result.json](portability-002/result.json), SHA-256
`40a94f2c5cf1d62a35d343f30c069ba55770c4292f008151af5dd814aa49c44c`,
hard-linked the pinned binary and 1,303 imported files beneath a different
installation root. The full retained-audit verifier passed there; changing one
local import or the local binary caused nonzero rejection while the historical
installation remained intact. A copy fallback supports separate filesystems.
`portability-001` retains the earlier hard-link-only probe and its original
source snapshot. These controls verify byte binding of the retained proof
evidence; they do not rerun the Lean proofs from the relocated installation.

The audit runner's failure-status unit controls use isolated stubs for a failed
job, failed direct build, failed version command and timeout. In each case it
retains an execution index with `FAIL` and `main()` returns 1; the command
entrypoint propagates that return value with `SystemExit`. A complete stubbed
execution reports `PASS` and returns 0. These tests check runner
behavior; they are not new theorem-prover evidence.

The append-only hotfix receipts are independently indexed by
[hotfix-snapshot.json](hotfix-snapshot.json), SHA-256
`423964376918eb3c56188a8a17d7709f891698beb394d5b47f36c1bc58e77b31`.
The [hotfix verifier](hotfix_verify.py) pins that digest and checks exact file
and directory membership, sizes, and hashes for the 65 files in
`binder-hardening-002` and `portability-002`. It also checks the current audit
runner and its CLI test source digests, the control scripts, accepted-audit
identity, and the expected outcome of every control. Run it
from the repository root with:

```sh
python3 formal/sonification/mat008/audit/hotfix_verify.py
python3 -m pytest tests/test_sonification_formal_mat008_audit_cli.py -q
```

The hotfix snapshot binds these two new control receipts. The original
`attempt-001` proof evidence remains governed by the pinned accepted audit
and the full verifier above. The snapshot adds no mathematical theorem or
Python implementation refinement claim.

The independently authored
[hotfix audit handoff](hotfix-independent-audit.json), SHA-256
`5661b7586dc045a69168803f9fc05162b858daa116fc0c8d1de85b0cb4059df0`,
records the reviewed source hashes and separately executed mutations. Its
PASS concerns the stated artifact and source binding only. The complete
accepted proof evidence still requires the full verifier and the pinned
Lean installation bytes.

Historical failed proof attempts remain untouched under `lean/attempts`; they are
explicitly outside the three-module active proof set. No commit, push, release,
publication, merge or historical-artifact edit was performed by this auditor.
