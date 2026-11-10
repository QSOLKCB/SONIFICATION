# MAT-008-REFINE-001: caller domain and Python semantic boundary

The production entrypoint does **not** enforce exact built-in list, dictionary
or string types. Those conditions are proposed premises for a conditional
ordinary-object semantic model. They are not established API guarantees, and
this inspection does not establish full CPython refinement.

## Frozen subject and inspected callers

The independently rechecked source identities are:

| Item | Identity |
| --- | --- |
| Formalization base | `ac1408cf0c459d79c3d0552287812a15ce644f0d` |
| Release | `mat-spec-008-v0.1.0` |
| Annotated tag object | `a02088e3c68addb41c9c7145694c0f566e84f87f` |
| Peeled production commit | `b4247877dd471e2e9d4986c86bdc1f11b14e43f8` |
| Source tree | `eb19f2e06a502442f621a73be1e5696c2fa25a65` |
| File | `materials/mat_spec_008.py` |
| Git blob | `3117adbc3739c834f8203d5d2dd2b80d6caf862b` |
| Module SHA-256 | `e56563235d87da43293bc46661b077660538b476d2bb340a1d208cc59aaa5f08` |

All three complete function bodies were inspected. SHA-256 here covers their
complete inclusive source-line spans, including final line endings.

| Symbol | Source lines | Source-span SHA-256 |
| --- | --- | --- |
| `_identity` | 69–75 | `8de0558da5d5324814881904302133e65ff1ba0fcb82f261d68744b5b3d445dc` |
| `_decimal` | 217–225 | `1813ff6c9f9be7b57199c94a325546466a3e038cf981a74e1b65171b1ccc0096` |
| `validate_future_measurement_packet` | 228–332 | `72c86ad19a4637dec04e05120786b001b2aefe9e3ff0e08f4f861e699959b247` |

At the frozen MAT-SPEC-008 release, direct calls to the future validator occur
in tests. `build_evidence` does not call it. At the formalization base,
`materials/mat_spec_009.py::check_future_challenge` is a production caller; its
call occurs at line 130. Additional callers are tests and the isolated-source
finite-conformance harness. `PYTHON_SEMANTICS.json` pins the inspected caller
files separately and retains exact inspection/probe commands and output.
Textual call-site search is not a proof of all possible dynamic Python calls.

## Conditions checked by callers, and conditions assumed for a model

| Condition | Actual source support | Classification |
| --- | --- | --- |
| MAT009 receives `isinstance(records, list)`, truthy input, `len(records) <= 10000` before calling MAT008 | Explicit wrapper checks | Checked expressions on this call path |
| Exact built-in list with stable iteration/length | Not enforced by `isinstance`; subclasses remain possible | Assumed for ordinary-object model |
| Every row is an exact built-in dictionary | MAT008 checks only `isinstance(row, dict)` | Assumed; malformed ordinary rows require modeled skip behavior |
| Every identity is an exact built-in string with ordinary hash/equality | `_identity` checks `isinstance(value, str)` and grammar, then returns the original object | Assumed; subclass counterexample below |
| Every row has five valid identity strings | The validator catches `ValueError` and continues on invalid identities | Not guaranteed; represent accepted-row projection explicitly |
| Ordinary fixture constructors create built-in lists/dicts/strings/bools | Literals, string operations and local constructors in tests, MAT009 `_synthetic_controls`, and finite harness | Source-constructor fact under normal bindings |
| All external inputs pass through ordinary `json.loads` without hooks | No such boundary is present in this entrypoint or its production caller | Unestablished; cannot use it as a caller guarantee |
| Stable inputs/globals, sufficient resources, ordinary CPython and stdlib behavior | Not enforced by these routines | Explicit residual assumptions |

For the proposed ordinary-object domain, dictionary keys and identity values
must be exact built-in strings, and field values must belong to the ordinary
finite JSON-like built-in type closure. No custom special methods may run.
A list may contain malformed ordinary rows if the model includes the production
skip paths. The domain must not silently be narrowed to healthy four-row
fixtures or structurally accepted packets.

## Complete production control flow and its modeling consequences

The function first evaluates `not records`. Falsy direct inputs such as `None`
return the same short blocked dictionary as `[]`. That return has two false
admission/authentication flags and an empty-packet reason; it has no
`heldout_accuracy`, candidate count or described-identity counts. Truthy direct
nonlists and generators may fail at iteration or the final `len(records)`.
The signature annotation does not prevent those calls.

For nonempty inputs, all owner dictionaries, phase sets and reason/count sets
are fresh local objects. Iteration follows the input iteration protocol. A
non-dictionary row adds a malformed-row reason and immediately continues.
For a dictionary row, the five `_identity` calls execute in campaign, lab, run,
document, row-ID order. The first `ValueError` adds an identity reason and
continues **before** updating row membership, campaign/lab counts or owner maps.
Other exceptions are not caught by this handler.

Consequently a source-refinement theorem about owner reuse must quantify over
rows that reach the ownership statements. One suitable projection preserves
input order and retains rows with the required ordinary representation whose
five identity calls succeed. It is false that every raw row's declared shared
run necessarily contributes a run-reuse reason: an invalid lab identity can
cause that row to be skipped. The packet can still be blocked for other reasons.
Final `candidate_rows` counts all raw input rows, including skipped ones.

For prefix-accepted rows, duplicate row IDs add a reason without skipping.
Campaigns and labs are added, campaign/lab consistency is checked, and the
campaign's source key `document + ':' + run` is compared and overwritten.
The delimiter is excluded by the ordinary identity grammar; using this as an
injective pair encoding still needs a corresponding mathematical lemma.
Run and document owner registries are then processed in that order. A prior
unequal campaign adds a reason, and the owner entry is overwritten. Reasons
are only added to throughout the function. Thus earlier detected conflicts
remain even after later owner-map overwrites; this is a source observation
awaiting a checked semantic induction.

Nonstring phases add an invalid-label reason and are replaced by the ordinary
string `INVALID` before insertion into phase sets. Declared source type and
diagnostic basis use equality. The synthetic marker uses **`is True`**.
Numeric checks call `_decimal` on value, measurement sigma and diagnostic sigma
in order within one `try`. The first `ValueError` prevents the remaining
numeric calls, adds one common reason, and execution proceeds to the digest
check. Hash ownership is updated only after digest type/grammar and pressure
condition checks pass.

After all rows, each recorded campaign must have exactly both declared phases;
at least two campaigns and labs and two distinct composite document/run keys
are required. The final status depends on whether the reason set is empty.
Reasons are sorted into a list; this removes reason-set iteration order from
the public output under ordinary string semantics. It does not by itself prove
universal determinism, permutation invariance or Python implementation fidelity.
Both admission/authentication flags are false; the nonempty path supplies
`heldout_accuracy: None`. These structural observations authenticate no
source document, digest ownership, experiment or physical phase.

## Helpers, runtime dependencies and observable rejection

`_identity` accepts nonempty ASCII `[A-Z0-9_]+` strings of at most 100 characters
that equal their stripped form. It performs no canonicalization and returns the
original input object. The codes are caller assertions; matching their grammar
does not establish source identity ownership.

`_decimal` accepts unsigned ASCII decimal strings, constructs `Fraction`, and
requires the value to be strictly positive. No float conversion occurs in that
body. JSON numeric literals, `None`, zero-valued strings and invalid spellings
are rejected. Missing and measured-zero values lead to the same public
uncertainty reason; this report does not preserve their distinction. A
syntax-valid long string can fail CPython's configured integer string-conversion
limit. That `ValueError` is caught by the validator's numeric handler.

The target calls `_identity` and `_decimal` plus ordinary str/dict/set/iteration,
regex and `Fraction` operations. Module import also loads earlier MAT-SPEC
modules and JSON constants. Isolating the three source functions supplies `re`
and `Fraction` directly and therefore does not prove whole-module import or
global-binding equivalence. Python parsing, bytecode compilation, builtins,
stdlib implementations, native libraries and resource/error semantics remain
part of the trust surface until separately justified.

No raw JSON or CSV parsing/serialization occurs in this function. In particular,
ordinary `json.loads` discards earlier duplicate object members using last-write
semantics. A packet text with an earlier synthetic source type followed by an
original-record source type can decode to a structural pass. A theorem about
all textual JSON fields requires a separately defined decoding boundary.

## Preserved subclass and boundary counterexamples

The following subclass is accepted by `_identity` and retained unchanged:

```python
class SaltedStr(str):
    def __new__(cls, text, salt):
        result = super().__new__(cls, text)
        result.salt = salt
        return result

    def __hash__(self):
        return super().__hash__() + self.salt
```

Give the first campaign's two otherwise healthy fixture rows
`SaltedStr('SHARED_RUN', 0)`, and the second campaign's rows
`SaltedStr('SHARED_RUN', 1)`. The run strings compare equal but have different
hashes. The extracted frozen validator returns
`STRUCTURAL_ONLY_UNAUTHENTICATED` with an empty reason list. An ordinary JSON
roundtrip converts them to exact built-in strings, and the same textual reuse
then returns `BLOCKED` with the run-reuse reason. This refutes a textual-owner
claim over arbitrary `isinstance(str)` values; exact-type or verified hash/equality
premises are material, not cosmetic.

Other freshly executed boundaries include `synthetic_fixture=1` and `'true'`
structurally passing where exact `True` blocks; dictionary/list subclasses
raising uncaught `RuntimeError` through overridden `get`/iteration; and invalid
identity rows being skipped before reuse tracking. No production change is
proposed by this domain analysis.

## Executed evidence and remaining bridge

The new probe command used observed **CPython 3.12.13**, retrieved the pinned
Git source, compiled only the three selected bodies, and executed **17 semantic
probes**, including assertions for subclass evasion, JSON-roundtrip rejection
and skipped-row behavior. Its exact `argv`, complete program, zero exit code,
original stdout/stderr and their SHA-256 digests are retained inline in
`PYTHON_SEMANTICS.json`. This is an executable semantic investigation; no
independent finite oracle or formal theorem was executed by that command.
Existing mathematical and conformance receipts remain separate and unchanged.

The next bridge must define the supported source AST's operational semantics;
relate exact strings and mutable Python maps/sets to mathematical representations;
model ordered helper calls, exceptions and `continue`; prove the accepted-row
ownership step and persistent reason invariant; and compose that result through
all later statements and both returns. Full-validator claims additionally need
numeric parser, regex, resource and whole-module initialization obligations.
Caller-derived and assumed premises must remain separately visible throughout.
`REFINEMENT_PROVED` and independent acceptance remain **OPEN**.

## Supplemental reproduction: campaign inequality override

An auditor identified a second independent subclass boundary. A new local
execution reproduced it against the same frozen source; the original 17-probe
command, stdout/stderr and digests above remain unchanged.

```python
class NeverUnequal(str):
    def __ne__(self, other):
        return False
```

Use the same healthy four-row fixture, assign campaign IDs
`NeverUnequal('C1')` and `NeverUnequal('C2')`, and use the exact built-in run
string `'SHARED_RUN'` for all four rows. The campaign texts differ, but Python
`left_campaign != right_campaign` evaluates to `False`. `_identity` returns
these original subclass objects unchanged. Consequently `owner[prior] != camp`
fails to detect the reused run, and the frozen validator returns
`STRUCTURAL_ONLY_UNAUTHENTICATED` with an empty reason list. Distinct labs,
documents, source digests and both phases were retained in the fixture.

An ordinary JSON roundtrip restores exact built-in campaign strings and the
same textual packet returns `BLOCKED` with
`REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS`. Exact built-in run keys alone therefore
do not justify the intended owner theorem: campaign values also need ordinary
string equality/inequality semantics, established through an exact-type premise
or a separately justified ingestion boundary.

The independently executed program, complete plain-data fixture, type
construction, source result and JSON-roundtrip result are retained in
`PYTHON_SEMANTICS.json::supplemental_executions`, ID
`CAMPAIGN_STR_SUBCLASS_NE_EVASION`. That command exited zero after asserting both
results. Its stdout SHA-256 is
`1d134b07cd39ca583e4ebe88c8bac27ebc6ca5b2e50c53412e28f67adc2ed3dc`.
The original 17-probe stdout SHA-256 remains
`3aa15b92a3f3fff9c424633b653528b79228b57d4a1452b820079dc6319f47e7`.
This is a counterexample to a broader Python-domain claim; it establishes no
universal refinement result and does not alter the source or earlier receipts.
