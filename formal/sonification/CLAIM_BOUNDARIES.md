# SONIFICATION-FORMAL-001 claim boundaries

The frozen production baseline is SONIFICATION commit
`8c62517138e3b86a4672d8969e190b747f81c398`. Historical tag objects, peeled
commits, trees and source bytes are separately pinned in SOURCE_MANIFEST.json.
A later formalization commit does not change the contents of those releases.

## Independent assurance layers

1. Mathematical proofs establish their exact stated propositions over their
   explicitly defined types. They do not establish Python correctness.
2. Python implementation refinement requires a checked source-to-semantics
   relationship, representation relation and observable-behavior theorem.
   Source hashes, AST inspection and a similar Lean definition do not discharge
   this requirement. Undischarged bridges remain OPEN.
3. Executable conformance establishes agreement only on the recorded corpus,
   interpreter and dependency versions. It is not universal refinement.
4. Digests establish byte identity under the trusted expected baseline and hash
   assumptions. They do not authenticate authors, experiments or execution.

Inventory membership is not proof coverage. Static source enumeration can miss
dynamic imports, callbacks, generated code and environmental dependencies;
the inventory records these limits. Every unexamined operation remains OPEN.
Independent human review of the intended specification is PENDING.

## Python semantic obligations

The outstanding bridge includes arbitrary-precision integers, Fraction parsing,
normalization and comparisons; Decimal/float conversions; string parsing;
Boolean short circuiting; indexing and collection order; sets and duplicate
handling; exceptions; JSON/CSV behavior; dependency versions; and observable
serialization where applicable. Restricting inputs must be stated, justified
and linked to production callers. A theorem for integer endpoints does not
cover arbitrary rational or floating point endpoints.

## MAT-SPEC-008 partial result

The `mat-spec-008-v0.1.0` run-ownership model has ten machine-checked Lean 4.19.0
theorems, including the universal finite-list statement
`Sonification.Mat008.reused_run_blocks`. Independent audit accepts those exact
mathematical statements and the recorded 1,296-case finite Python observation.
The model uses Lean String equality and an association-list owner map. It does
not prove that the frozen Python dictionary scan refines that map.

The finite Python tests use exact built-in dict and string rows. Equal-text
`str` subclasses with inconsistent hashes provide a counterexample to an
unrestricted Python-object version of the run-reuse claim. The accepted finite
domain does not silently become a precondition for universal Python
correctness. `REFINEMENT_PROVED` remains OPEN for the run gate and the complete
MAT-SPEC-008 validator. The remaining source-identity, row, diagnostic,
missingness, eligibility and evidence-admission obligations remain OPEN.

## Historical proof evidence

SPARK-002 Phase 1A retains its owner-executed GNATprove receipt for 23/23
reported checks at `06b1294bf1617e9eb3b825051e8bfbf7470e395c`.
Phase 1B retains its receipt for 9/9 reported checks at
`6f0f1be1ba8885fa708d7328bcb92fbf4ecc324f`. These are historical SPARK
source-specific results. No receipt is replaced or promoted into a Python proof.

## Scientific and publication limits

MAT-SPEC remains `NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES`.
There is no MAT-SPEC-011. Software proofs do not establish independent helium
experiments, calibrated physical uncertainty, classifier accuracy, auditory
discrimination or E8 physical theory. Mandatory blocked gates retain their
original scientific meaning.

Existing DOI identities remain `10.5281/zenodo.24089846` (MAT-SPEC version)
and `10.5281/zenodo.24090762` (SPARK-001 software). Publication, DOI reservation,
release/tag changes and PR merges require explicit owner authorization.
Root ETQ processing remains symbolic; no sampled audio is generated.

The private formalization protocol is pinned at
`a1f74e8d1847d218d6b68c125fac9522e2ffc2fb`. Its schemas, templates, bundles
and project packets remain outside this public tree. Public artifacts here
are independently authored. Protocol validation provides planning checks;
it has no theorem-prover or proof-acceptance authority.
