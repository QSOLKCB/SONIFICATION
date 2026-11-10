# MAT-008-REFINE-001 contract

This contract concerns one reason emitted by the frozen
`validate_future_measurement_packet` body: `REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS`.
It separates source syntax, an abstract map transition, actual Python execution,
and the accepted Lean run-ownership model. A checked theorem about the abstract
transition is a **conditional model result** until the source and CPython
semantic bridges are discharged.

## Frozen target and selected source path

The production release is annotated tag object
`a02088e3c68addb41c9c7145694c0f566e84f87f`, peeled commit
`b4247877dd471e2e9d4986c86bdc1f11b14e43f8`, source tree
`eb19f2e06a502442f621a73be1e5696c2fa25a65`, and blob
`3117adbc3739c834f8203d5d2dd2b80d6caf862b`. The exact bytes of
`materials/mat_spec_008.py` have SHA-256
`e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08`.
The existing `../SOURCE_BINDING.json` records 14 historical context files.
The new `SOURCE_BINDING.json` and `source_bind.py` bind eight selected AST source
spans, the five identity calls, the two ownership iterations, the reason-set
observation and the full frozen source bytes. The protocol context is held
separately at `a1f74e8d1847d218d6b68c125fac9522e2ffc2fb`.

The selected path is:

1. A falsy `records` value returns a short `BLOCKED` report before any owner
   map exists. A nonempty input proceeds to fresh dictionaries and a fresh
   `reasons = set()`.
2. Each iterated row failing `isinstance(row, dict)` adds
   `MALFORMED_CANDIDATE_RECORD` and continues. Otherwise `_identity` is called
   in campaign, laboratory, run, document, row-ID order. A caught `ValueError`
   adds `MISSING_OR_INVALID_SOURCE_IDENTITIES` and continues. No ownership
   update occurs on either path.
3. A row passing all five calls reaches several row and campaign checks. A
   duplicate row ID adds a reason but **does not skip** ownership. The run and
   document iterations execute in that order. For each tuple, `prior in owner`
   short-circuits the later `owner[prior] != camp` expression. If both are
   true, `reasons.add(key)` executes. `owner[prior] = camp` then executes
   unconditionally, including after a mismatch.
4. Phase, source-kind, diagnostic, decimal and digest checks follow the owner
   update. They add other reasons and may take their documented rejection
   paths. At a normal nonempty return, the observable reason list is
   `sorted(reasons)`. No statement in this frozen body removes a reason.

`_identity` uses `isinstance(value, str)`, a length and strip check, and
`re.fullmatch`; it returns the **same object**, including a valid `str`
subclass. Its `ValueError` is caught at the identity prefix. Other exceptions
from overridden methods can escape. `_decimal` uses exact decimal spelling,
`Fraction`, and a positive comparison. Its `ValueError` is caught later; its
numeric result does not affect the already executed run owner update. This
slice does not model the complete validator, module initialization, or
physical-evidence admission.

Python's [expression evaluation order](https://docs.python.org/3.14/reference/expressions.html#evaluation-order),
[short-circuit Boolean operations](https://docs.python.org/3.14/library/stdtypes.html#boolean-operations-and-or-not),
[dictionary semantics](https://docs.python.org/3.14/library/stdtypes.html#mapping-types-dict),
and [compound-statement control flow](https://docs.python.org/3.14/reference/compound_stmts.html)
inform this interpretation. Documentation is a semantic reference, not a
machine-checked CPython-to-Lean proof.

## Input domain and accepted-row projection

Let `P(records)` be the **ordered** sequence of rows that actually reach the
run/document gate. It excludes non-dictionary rows and rows for which one of
the five `_identity` calls raises the caught `ValueError`. It retains repeated
row IDs and rows rejected by a later phase, measurement, source or digest
check. Each projected Lean `ParsedRow` has the campaign and original-run
strings from that row. A theorem over arbitrary raw records is false: a row
with an invalid laboratory identity may declare a shared run but never enter
the owner gate.

| Domain class | Evidence or premise |
| --- | --- |
| Caller checked | MAT009 checks `isinstance(records, list)`, truthiness and length at most 10,000 before this call. It does not check exact built-in types or validate every row. |
| Constructor supported | The recorded synthetic fixtures are created with built-in list/dict/string literals under normal bindings. This is a fact about those constructors, not all callers. |
| Assumed for conditional abstract correspondence | Exact built-in list containing exact built-in row dictionaries or ordinary malformed values; exact built-in strings for identities in processed rows; ordinary stable builtins and helper globals; no custom dispatch, concurrent mutation or resource failure. |
| Excluded from that premise | `str` subclasses with inconsistent hashes or overridden comparison, list/dict subclasses with overridden methods, arbitrary iterables, monkeypatching and adversarial tracing. These remain part of the unrestricted Python API. |

See `CALLER_DOMAIN.md` and `PYTHON_SEMANTICS.json` for inspected call sites,
exact input examples, complete frozen control flow and executed
counterexamples. A JSON roundtrip normalizes the recorded subclass examples,
but no production caller is proven to apply such a roundtrip.

## Model, relation and exact obligations

The accepted model in `../lean/Mat008/RunOwnership.lean` defines `ParsedRow`,
`State`, `lookup`, `step`, `scanFrom` and `scan`. Its `owner` is a newest-first
association list; its `conflict` is sticky. The new abstract Python state is a
functional finite-map observation and a Boolean membership bit for the run
reason. `REPRESENTATION_RELATION.md` defines their pointwise relation. It
does **not** identify the Lean function with CPython's mutable `dict`.

The requested obligations are interpreted as follows:

| ID | Exact intended scope |
| --- | --- |
| R1 | Empty abstract owner map and absent run reason relate to `initial`. |
| R2 | For every string key, related abstract lookup and Lean `lookup` agree. The actual Python `dict` observation remains a separate semantic premise. |
| R3 | For every related state and processed row, abstract overwrite after the membership/comparison guard relates to Lean's newest-pair `step` owner. |
| R4 | For every related state and processed row, abstract run-reason membership after the step equals Lean's conflict flag after `step`. This includes a reason already present. |
| R5 | An abstract run reason already present remains present after every later processed row. |
| R6 | For every finite ordered processed-row sequence, the abstract fold from a related state relates to `scanFrom` on the same rows. |
| R7 | Given R1–R6 and the accepted `reused_run_blocks` theorem, a pair of processed rows with equal runs and unequal campaigns forces the abstract reason bit. A claim about the actual returned Python reason additionally requires the open semantic/observation bridge and normal return. |

The quantifiers in R2–R7 range over **all Lean strings and finite processed-row
lists** unless an exact theorem type says otherwise. They do not range over
all Python objects or all raw packets. The code and checked theorem types are
the authority for the achieved subset; this prose cannot promote an omitted
or weakened theorem.

## Source-sensitive method and remaining trust

`source_bind.py` checks exact Git tag/commit/tree/blob identity and SHA-256,
the prior source manifest and accepted Lean source, selected source spans, and
the AST shapes of the non-dict skip, five identity calls, short-circuit gate,
owner overwrite and reason return. It can separately require the checked-out
module to match the frozen bytes. Its parser, structural matcher and manually
chosen gate interpretation are **trusted source-analysis code**. A digest
match proves byte identity, not behavioral refinement.

The Lean bridge, if checked, proves properties of a separately defined
abstract transition. It does not prove that `ast.parse`, Python compilation,
CPython dictionary/string/set operations, exceptions or control-flow execution
implement that transition. In particular, the following remain OPEN:

- A checked semantics for the relevant frozen Python AST, including exact
  `and`, `in`, `!=`, subscript, assignment, tuple iteration, `try`/`continue`
  and method-call behavior.
- A verified or independently accepted source-to-semantic-term translation,
  or a source-sensitive proof directly over that AST semantics. The current
  source binder is executable syntax evidence, not a verified translator.
- A proof that exact built-in CPython strings and dictionaries satisfy the
  abstract equality, hashing, membership, lookup, overwrite and reason-set
  rules under the declared interpreter/version assumptions.
- Composition through the whole validator, all later statements and both
  return paths, including normal termination, exception behavior and the
  sorted observable reason list.
- A caller guarantee for the exact built-in input domain. MAT009 currently
  supplies no such general guarantee.

Until these bridges are discharged, `REFINEMENT_PROVED` remains **OPEN** even
if source binding, Lean abstract-state theorems, finite tests and independent
audit all pass. A run-reuse reason is distinct from the overall `BLOCKED`
status: unrelated reasons can block a packet, and a structural pass never
authenticates physical evidence.
