# MAT-008-REFINE-001: run-ownership correspondence

This slice studies the `REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS` reason in the
frozen MAT-SPEC-008 `validate_future_measurement_packet` implementation. Its
result is **partial**: the new Lean proofs establish a conditional relation
between two mathematical ownership-state models. The frozen Python source is
bound to exact bytes and selected AST syntax; the link from actual CPython
execution to the mathematical transition remains **OPEN**.

The annotated release tag object is
`a02088e3c68addb41c9c7145694c0f566e84f87f`, peeled commit
`b4247877dd471e2e9d4986c86bdc1f11b14e43f8`, source blob
`3117adbc3739c834f8203d5d2dd2b80d6caf862b`, and
`materials/mat_spec_008.py` SHA-256
`e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08`.
The formalization starts from main commit
`ac1408cf0c459d79c3d0552287812a15ce644f0d`. Historical source, accepted
proofs, receipts and release artifacts are unchanged.

## What the checked result says

The accepted MAT008 model uses a newest-first association list and a sticky
conflict flag. The new `AbstractPy` model uses a functional owner map, a reason
membership function and an ordered list of **already processed** rows. The
name describes the intended abstraction target, not a verified Python
interpreter. `Related` requires pointwise owner-lookup equality and equality
between the run-reuse membership bit and model conflict flag.

Lean 4.19.0 checks the empty-state relation; lookup under an explicit related
prestate; owner overwrite including repeated keys; reason-bit equivalence and
persistence; arbitrary finite ordered scans; and the abstract consequence of
two processed rows sharing a run across campaigns. A typed consumer checks
the exact 26 intended theorem statements. The theorem, axiom and trust
inventory is in `lean/theorem-statements.json`, `lean/HANDOFF.json` and
`lean/README.md`. These counts are mathematical statements, not Python
refinement results.

The source binder checks the frozen tag, commit, tree, blob, complete module
hash, prior binding and accepted model hash. It checks selected AST nodes for
row iteration, non-dictionary/invalid-identity skips, ordered identity calls,
the run/document ownership loop, initial states and reason observation. This
is source-sensitive **syntax evidence**. Its manually chosen AST-to-operation
interpretation and the semantics of actual built-in Python objects are
trusted assumptions, not Lean theorems.

The [contract](REFINEMENT_CONTRACT.md),
[representation relation](REPRESENTATION_RELATION.md),
[caller-domain analysis](CALLER_DOMAIN.md) and
[status inventory](REFINEMENT_STATUS.json) delimit every claim. The exact
source binding is in [SOURCE_BINDING.json](SOURCE_BINDING.json), with executable
checker [source_bind.py](source_bind.py).

## Domain and counterexamples

The accepted-row projection excludes non-dictionary records and rows whose
five ordered `_identity` calls raise the caught `ValueError`. It keeps rows
with duplicate row IDs or later-invalid measurements because they reach the
ownership loop. Row order determines the final owner; prior conflicts remain
sticky in the abstract model.

MAT009's production caller checks that `records` is a `list`, is nonempty and
has at most 10,000 elements. It does not require exact built-in lists,
dictionaries or strings. `_identity` accepts `str` subclasses and returns the
same object. The retained Python probes show two distinct broader-domain
failures: equal-text run subclasses with inconsistent hashes can evade reuse
detection, and campaign subclasses overriding `__ne__` can suppress the
comparison. JSON normalization removes those subclasses in the probes, but no
general production caller guarantee for such normalization was found.

Finite tests execute the exact frozen function bodies under the recorded
interpreter and compare the run reason against an independent pairwise oracle
on explicitly identified processed rows. They include same-campaign repeats,
cross-campaign conflicts, repeated overwrites, early and late conflicts,
reordered rows, skipped invalid identities and the two subclass
counterexamples. The prior MAT008 milestone retains its independent
1,296-case corpus. No finite test establishes a universal Python theorem.

## Reproduction

Use the pinned Lean 4.19.0 toolchain, or supply the same pinned distribution at
another local path. From the repository root:

```sh
python3 formal/sonification/mat008/refinement/source_bind.py --check-worktree
python3 -m unittest discover -s tests \
  -p test_sonification_formal_mat008_refinement.py -v
python3 formal/sonification/mat008/refinement/lean/check.py \
  --lean /path/to/lean-4.19.0/bin/lean --out /tmp/mat008-refine-new-check
python3 formal/sonification/mat008/refinement/lean/negative.py \
  --lean /path/to/lean-4.19.0/bin/lean --out /tmp/mat008-refine-new-negative
python3 formal/sonification/mat008/refinement/lean/verify.py \
  --lean /path/to/lean-4.19.0/bin/lean --out /tmp/mat008-refine-new-retained-check
python3 formal/sonification/mat008/refinement/lean/verify_negative.py \
  --lean /path/to/lean-4.19.0/bin/lean --out /tmp/mat008-refine-new-retained-tamper
```

All four Lean proof and evidence runners require **new** output directories; they never overwrite
earlier attempts. After a source commit, `check.py --baseline-commit
FULL_40_CHARACTER_SHA` additionally binds every proof/checker input to that
commit. `evidence.py run --baseline-commit FULL_40_CHARACTER_SHA --out
/tmp/mat008-refine-new-execution` captures the source binding and focused
Python tests with original stdout/stderr. `evidence.py verify RECEIPT_DIR
--receipt-commit FULL_40_CHARACTER_SHA` checks those logs against the exact
evidence Git commit and checks the test/checker dependency inputs against
their earlier source commit. The original development
attempts, including rejected proofs, are preserved under `lean/attempts/`.
The retained-evidence verifier maps recorded Lean imports onto the supplied
local toolchain root and checks their pinned digests; the auditor's absolute
installation path is only historical metadata.

The private formalization-context protocol was read at
`a1f74e8d1847d218d6b68c125fac9522e2ffc2fb`. Its focused planning packet
was validated and bundled in a separate private worktree. It is neither copied
here nor treated as a theorem prover or acceptance authority.

## Assurance boundary and next obligation

`MODEL_PROVED` applies to the new abstract-state theorems only.
`DIFFERENTIAL_TESTED` applies to the retained finite cases.
`REFINEMENT_PROVED` remains `OPEN`. Independent acceptance applies only to the
scope stated in the retained audit report; it cannot imply Python refinement.

The next smallest source-refinement obligation is a checked connection from
the frozen gate AST to the three abstract instructions for **exact built-in**
identity strings and dictionaries, with missing-key and overwrite behavior
spelled out. That bridge must also state what is trusted about CPython; the
subsequent projection and final-return obligations remain separate. This
software work cannot authenticate physical experiments or close scientific
gates.
