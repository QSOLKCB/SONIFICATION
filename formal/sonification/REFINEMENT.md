# First Python source-refinement investigation

The universal refinement obligation is **OPEN**. No theorem in this increment
establishes that CPython's execution of the frozen MAT-SPEC implementation
refines a Lean specification. The executed result is **finite conformance of a
source-pinned, extracted production function body**, plus rejection of source
and syntax mutations. The AST adapter is an auditable experimental bridge;
its semantics have not been proved equivalent to CPython.

## Exact subject

| Identity | Value |
| --- | --- |
| Release | `mat-spec-007-v0.1.0` |
| Annotated tag object | `8b933a5ab09b8e76afe4c8e169e089f251e23314` |
| Peeled production commit | `b97348ff8fcf3f57764dec21a8914f153f96a745` |
| Production source tree | `c1b842c6bace3ccb01714007b8d7ebb05bcecd31` |
| Module | `materials/mat_spec_007.py` |
| Module SHA-256 | `2e363adea6c781ab68aec69d2ee5c7d712fc5e46346ae5be21d8cf3e929781c6` |
| Function | `classify`, source lines 173–180 |
| Exact function bytes SHA-256 | `0be0b19a40a953200213f7577c1ed7fdea563c48dc1d86f2ae400c40f681dba2` |

The adapter retrieves this commit with `git show`; it does not load a moving
branch. Its independent hard-coded expected tag object, commit, tree and module
digest prevent the generated inventory from authorizing a changed target.
Production files and releases are untouched. Original SPARK proof receipts
are not inputs to this investigation and establish no Python correspondence.

## Intended contract and representation

For endpoint values `a0`, `a1`, `b0`, `b1` in the mathematical rationals, each
Python input is an exact, two-element built-in `tuple`; every element has
`type(x) is fractions.Fraction`. The representation relation is
`q = x.numerator / x.denominator`, with a positive denominator and ordinary
CPython `Fraction` behavior. It is a **proposed representation relation**, not
an independently accepted refinement theorem.

For all such inputs, the intended observable behavior is:

- If `a0 > a1` or `b0 > b1`, raise `ValueError` with the exact production
  message `invalid reported-fit interval` before classifying any separation.
- Otherwise return `a_below_b` when `a1 < b0`, return `b_below_a` when
  `b1 < a0`, and return `overlap` otherwise.
- Closed intervals with touching endpoints overlap. A singleton at zero is
  valid. Missing endpoints are outside this exact-Fraction domain; the explicit
  `None` negative test observes `TypeError` rather than zero coercion.

This specification is independently authored from the public production body.
Independent mathematical and implementation review remains pending. It does
not impose positivity on endpoints or require intervals to be disjoint.
Invalid intervals are included as explicit rejection obligations, so the
finite experiment is not restricted to successful return paths.

## Implemented experimental method

`refinement/source_adapter.py` checks the complete pinned module bytes, parses
it with the observed CPython AST implementation, finds exactly one top-level
`classify` definition, and compares its complete AST (including arguments,
annotations and branches) with a closed syntax contract. It compiles that
extracted source function with the ordinary `Fraction` and `ValueError`
bindings. It neither executes module initializers nor invokes a production
export pipeline. This distinction leaves whole-module initialization and
dependency interactions OPEN.

The second evaluator walks the accepted source AST. Its supported syntax is
ordered `if`, short-circuit `or`, indexed tuple reads at constants `0` and `1`,
strict `<` and `>` comparisons, exact string returns, and the one declared
`ValueError` rejection. It explicitly rejects lists, tuple length changes,
`Fraction` subclasses, extra calls and any changed AST. It does not infer
correctness from AST similarity.

A separately authored oracle compares rational endpoints by integer
cross-products of numerators and positive denominators. It uses no `Fraction`
ordering, decimal-to-float conversion or floating tolerance. All three outcomes
are compared exactly: returned string, or exception class and message.

The ordinary tuple and exact `Fraction` restriction removes application-level
operator overrides. This is a justified scope restriction, not a hidden
assumption that Python annotations enforce this domain.

## Executed finite evidence

The recorded CPython version is **3.12.13**. Its actual executable path and
SHA-256, `fractions`, `numbers` and `ast` source-file hashes, commands, working
directory, timestamps and dirty worktree status are in
`refinement/receipts/final-conformance/receipt.json`. Input source snapshots are
retained next to the logs. No claim is made that these hashes authenticate the
machine or independently attest its execution.

The finite endpoint set is the 15 distinct values of `Fraction(n,d)` for
`-3 <= n <= 3`, `1 <= d <= 3`, sorted by exact value. Every ordered endpoint
quadruple is exercised: **50,625 cases**, including reversed endpoints.
Five additional cases exercise adjacent 4096-bit integers, tiny positive
rational denominators, touching, containment and reversed endpoints. The
corpus has **50,630 cases**, zero mismatches and SHA-256
`34ddbea814f45f7e821104959813e538dcea6823b2c514fb64ca7cc1272d8585`.
The digest covers case identity, oracle, compiled-body and AST-evaluator
outcomes in the declared order; the deterministic generator reconstructs it.

| Observed outcome | Case count |
| --- | ---: |
| `ValueError` | 36,226 |
| `a_below_b` | 2,382 |
| `b_below_a` | 2,380 |
| `overlap` | 9,642 |

**17 executable tests** pass in the final receipt. They include rejection of a
changed production source, changed comparison, weakened invalidity guard and
prohibited call; execution of comparison, exception and return-label mutants;
detection of an altered expected result; and explicit missing/truncated-input
observations. Missing and malformed arguments are out-of-contract examples,
not a universal theorem about all rejection paths.

Earlier `initial-conformance` and `reviewed-conformance` receipts are retained
unchanged. They precede formatting and receipt-capture improvements; their
input hashes are recorded but their full script snapshots were not retained.
They are superseded for replay by `final-conformance`, which includes exact
input snapshots. None is formal-refinement evidence.

## Preserved counterexample to an overbroad interpretation

Python annotations allow a caller to supply a `Fraction` subclass with changed
comparison behavior. The test
`test_runtime_annotations_do_not_prevent_overridden_order` executes this minimal
example against the extracted frozen function:

```python
class FalseOrdering(Fraction):
    def __lt__(self, other):
        return False

a = (FalseOrdering(0), FalseOrdering(0))
b = (Fraction(1), Fraction(1))
```

Production returns `overlap`, while the rational-value oracle returns
`a_below_b`. Thus a proposed theorem over all values accepted by the annotation,
or all `isinstance(x, Fraction)` values, would be false without an ordinary
operator-semantics condition. This is not a reported defect in validated
MAT-SPEC source rows. The current adapter rejects the subclass case.

## Remaining obligations and trust

The investigation establishes **no full, conditional or bounded formal
implementation-refinement theorem**. Finite conformance has a bounded input
corpus; that is not bounded formal verification.

The missing obligations are precise:

1. Give a formal operational semantics for this Python subset, including tuple
   subscription, immutable ordinary `Fraction` objects, exact integer
   comparison, evaluation order, short-circuiting, returns and exceptions.
2. Prove a source-sensitive translation or certificate checker correct relative
   to that semantics. Parsing and compilation are currently trusted software.
3. Prove representation preservation from CPython arbitrary-precision integers
   and normalized `fractions.Fraction` to mathematical rationals. This requires
   the relevant stdlib implementation and version-specific dependency closure,
   or an explicit external-provider assumption accepted for a conditional claim.
4. Prove initial-state and observable-result relations to the Lean mathematical
   specification. There is currently no machine-checked link between these
   experimental Python adapters and the Lean definitions.
5. State and justify resource, allocation, tracing, monkey-patching and runtime
   environment assumptions; establish whole-module import/global binding
   obligations for a claim about production module execution.
6. Extend separately to `decimal`, `interval` and `pairwise_fits`, including
   regular-expression acceptance, string parsing, dictionary lookup and missing
   keys, positive-error checks, combinations order, duplicates, counts and
   rejection paths. JSON/CSV parsing, serialization and provenance remain
   separate OPEN obligations.

No proprietary protocol text or templates are redistributed by these files.
The public artifacts were independently authored for this target.

## Reproduction

From the repository root, with historical Git objects and tags available:

```sh
uv run --no-project --python 3.12 formal/sonification/refinement/run.py
uv run --no-project --python 3.12 -m unittest discover -s formal/sonification/refinement -p test_refinement.py -v
uv run --no-project --python 3.12 formal/sonification/refinement/capture.py --receipt-dir /tmp/sonification-formal-new-receipt
```

The capture command refuses to overwrite an existing receipt directory.
Interpreter release selection must be checked against the recorded banner and
digest when reproducing the precise historical environment; `--python 3.12`
selects a compatible local interpreter and does not itself freeze a patch release.

## Extended interval-construction investigation

`refinement/test_interval.py` also extracts the exact frozen `decimal` and
`interval` bodies under separate closed AST contracts. The source module
identity above remains their baseline. The ordinary source call chain is
`pairwise_fits -> interval -> decimal -> Fraction`, followed by `classify`;
reversal passes the same tuples and scaling constructs new ordinary `Fraction`
endpoints through multiplication by the integer `2`. This is a source
inspection finding, not a theorem about Python global bindings or imports.

The extension executes **42 decimal parsing cases** (21 authored strings under
each `positive` flag) and **882 interval-construction cases** (both declared
fields crossed with all 21 center and 21 error strings). The independent
parser recognizes the decimal grammar by ASCII character inspection and builds
an integer coefficient and power-of-ten denominator without regular expressions
or `Fraction(text)`. The interval oracle constructs endpoint numerators by
integer arithmetic, independently of production `Fraction` addition/subtraction.
Cases cover negative and measured-zero centers, decimal trailing zeros, signs,
leading zeros, whitespace, exponent/rational spellings, Unicode digit rejection,
empty strings, invalid fields, missing keys and `None`. Two additional source
mutations change the interval subtraction and weaken positive-error rejection;
the AST contracts reject both.

A second executable counterexample shows why a grammar-only totality theorem
would be false for arbitrarily long strings on the observed interpreter.
`sys.get_int_max_str_digits()` is nonzero; a positive decimal string with one
more digit than that configured bound matches the declared regular expression
but the production `Fraction(text)` conversion raises `ValueError`. The
independent integer-accumulation oracle accepts that grammar instance. The
experiment changes no interpreter setting. The test explicitly skips this
configuration-dependent counterexample if the observed interpreter disables
that bound. Full decimal semantics must include the actual conversion bound
and other rejection/resource behavior, rather than silently assuming all
syntactically valid decimal strings convert.

The current complete investigation receipt is
`refinement/receipts/expanded-final-conformance/receipt.json`: **50,630 classify
cases**, **924 supplemental decimal/interval cases**, and **26 executable tests**
pass. This receipt captures current source snapshots and adds the actual
`re`, regex-parser/compiler/constants file identities to the trusted stdlib
inventory. It supersedes earlier investigation receipts without rewriting them.
The transitive CPython/native-library dependency closure remains an explicit
trust and investigation boundary.

For the four independent assurance dimensions of this investigation:

| Dimension | Current result |
| --- | --- |
| `MODEL_PROVED` | Not claimed by these Python artifacts; see separate Lean evidence |
| `REFINEMENT_PROVED` | False / OPEN |
| `DIFFERENTIAL_TESTED` | True for the exact finite domains and interpreter above |
| `AUDIT_ACCEPTED` | False; independent acceptance is pending |

A passing test, syntax check, source pin, or mathematical model theorem never
promotes another dimension. `refinement/handoff.json` retains the commands,
source identities, outcomes, blockers and next operation for resumption.
