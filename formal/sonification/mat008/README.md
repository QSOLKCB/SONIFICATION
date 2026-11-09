# MAT-SPEC-008 run-ownership slice

This slice concerns the original-run reuse gate in
`materials/mat_spec_008.py::validate_future_measurement_packet`. The frozen
release is annotated tag object
`a02088e3c68addb41c9c7145694c0f566e84f87f`, peeled commit
`b4247877dd471e2e9d4986c86bdc1f11b14e43f8`, tree
`eb19f2e06a502442f621a73be1e5696c2fa25a65`, and module SHA-256
`e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08`.
`SOURCE_BINDING.json` records the target and helper spans, Git blobs, and 14
context-file identities. It does not establish Python behavior.
The generated `PROOF_INVENTORY.md` keeps the complete validator OPEN; the
canonical `theorem-map.json` has separate rows for this scoped result.

| Assurance dimension | State | Exact scope |
| --- | --- | --- |
| `MODEL_PROVED` | PASS | Ten Lean theorems about an independent run-owner model |
| `REFINEMENT_PROVED` | OPEN | No source-to-model correspondence theorem |
| `DIFFERENTIAL_TESTED` | PASS | 1,296 exact built-in four-row cases and named controls |
| `AUDIT_ACCEPTED` | PASS | Independent audit of those exact model and finite claims |

The main theorem is `Sonification.Mat008.reused_run_blocks`. For every finite
list of `ParsedRow` values and any two member rows, equal original-run strings
and different campaign strings force the final model conflict flag to `true`.
It has no row-count bound. The exact Lean type, nine supporting theorem types,
and transitive axiom sets are in `lean/theorem-statements.json`. Only `propext`,
`Quot.sound`, and `Classical.choice` occur in the accepted final closure. The
Lean kernel, distribution, runner, operating system, and recorded digest
checks remain trusted. See [lean/README.md](lean/README.md).

The finite conformance program selects three exact function bodies from the
frozen Python module, compiles them with CPython, and compares the run-reuse
reason to a separately authored pairwise oracle. The independent auditor also
used a grouping oracle. A `str` subclass with equal text but inconsistent
hashes evades the production dictionary gate; JSON-decoded built-in strings
restore blocking. A numeric `synthetic_fixture=1` passes the structural flag
check, while physical evidence admission remains false. These counterexamples
bound the Python observations; they do not alter the mathematical theorem.

## Reproduce the retained evidence

From a full-history checkout with the pinned Lean 4.19.0 toolchain available:

```sh
python3 formal/sonification/mat008/verify_source_binding.py
python3 formal/sonification/mat008/verify_receipt.py
python3 formal/sonification/mat008/audit/verify.py attempt-001 \
  --lean-root /absolute/path/to/lean-4.19.0
python3 -m pytest tests/test_sonification_formal_mat008_run_ownership.py -q
```

The accepted audit report is `audit/attempt-001/AUDIT.json`, SHA-256
`34eef078032bfb168faec6ba3bfe82cbf7e6bdc0412fe56820bc2bf2e26665d8`.
The hardened verifier pins that report and all 161 referenced evidence files.
Four model mutations and 14 isolated binder mutations were detected; original
commands and logs are retained in the `lean/attempts`, `audit/attempt-001`, and
`audit/binder-hardening-001` directories. The earlier
`lean/EVIDENCE_MANIFEST.json` inventories the development attempt files at its
creation point; the postcommit receipts are separately bound by the accepted
audit. No historical proof receipt is rewritten.

The current verifier accepts `--lean-root` so an identical pinned Lean 4.19.0
installation can live at another absolute path. It checks the local binary
and all 1,303 imported `.olean` digests without opening the archived absolute
paths. The current verifier's 14 binder controls are retained in
`audit/binder-hardening-002`; three relocation controls are in
`audit/portability-002`. Their 65 retained files are bound by
`audit/hotfix-snapshot.json`; the verification command is in
[audit/README.md](audit/README.md).
The audit runner now exits nonzero when a job fails or times out, after
writing its execution index. The original accepted audit report remains
byte-for-byte unchanged.

The unit tests check byte identity of the current checkout source and context
files and run the finite oracle on those checked bytes. This works with a
shallow Actions checkout. A shallow checkout cannot independently re-resolve
the historical tag object, commit, or tree. The full-history source-binding
command above performs that separate Git check. The retained finite receipt
also records its original full-history source check.

The complete MAT-SPEC-008 packet validator remains OPEN: row eligibility,
missingness, diagnostics, document and digest ownership, source authenticity,
physical admission, and observable Python semantics need further work. The
model proof and finite tests do not establish CPython refinement or scientific
independence. See [audit/README.md](audit/README.md) for audit commands and
limitations.
