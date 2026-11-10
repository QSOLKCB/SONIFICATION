# MAT009 caller domain and bridge limits

This analysis concerns the frozen MAT009 `check_future_challenge` function and
its direct MAT008 validator call. `CONTRACT.md` gives the source order and
reason conditions. The source binder confirms bytes and selected syntax only.
No theorem about the behavior of arbitrary CPython objects follows from that
binding, and no metadata in this packet authenticates physical experiments.

## A tractable exact built-in domain

For a model of the normal row-scan path, a narrow input domain is:

1. `type(records) is list` and `1 <= len(records) <= 10000`.
2. Every element has `type(row) is dict`; every key has `type(key) is str`.
   Every value read by either validator has exact type `str`, `bool`, or
   `NoneType`, and all string identities used as map or set keys have exact
   type `str`. Missing keys produce the ordinary `None` from built-in
   `dict.get`.
3. The list and dictionaries are not mutated while the call runs. The imported
   modules, built-ins, regex objects, and `Fraction` implementation are not
   monkeypatched during the call.

This domain permits malformed text, absent fields, and both exact Boolean
values, so it can model negative reasons. A still narrower passing fixture
also supplies the required field texts, two disjoint campaign/lab families,
both phases in each partition and campaign, distinct source and diagnostic
identities, and one shared syntactically valid receipt. Passing those
structural assertions does not authenticate any experiment or preregistration.

On this domain, built-in strings obey ordinary textual equality and
hash-consistency, and built-in dictionaries and sets provide the expected
lookup and intersection behavior. A source-to-model bridge would still need
to establish, rather than assume, the following:

- The MAT008 parent result for the *same* input list, including its skip paths
  and sorted reasons. The MAT009 child only imports that reason list.
- The MAT009 early result shape, three child skip paths, and state-update
  order. Parent eligibility is different: MAT008 requires five identities;
  MAT009 requires only campaign and lab after role acceptance.
- Campaign role conflict, split campaign/lab/phase sets, both independent
  diagnostic owner maps, valid receipt set, final checks, sorted reason union,
  and the constant nonadmission result fields.
- The exact behavior of Python `isinstance`, regular expressions,
  `Fraction`, `dict.setdefault`, dictionary overwrite, set intersection, and
  sorted strings in the chosen interpreter. `SOURCE_BINDING.json` does not
  supply these semantic lemmas.

The MAT008 validator itself is still only a structural metadata check. A
future refinement theorem must not turn a structural pass into a claim of
source independence, a real holdout, classifier performance, or physical
validation.

## Why the exact-type boundary matters

The released source uses `isinstance`, not exact type tests. Consequently it
accepts subclasses at its outer list check, its row dictionary check, and its
identifier/digest checks. The finite tests retain these concrete observations:

| Outside-domain input | Frozen CPython observation | Consequence |
| --- | --- | --- |
| Two `str` subclass campaign IDs with equal text `SAME_CAMP` but hashes 11 and 23, one object reused within each split | `_identifier` and MAT008 `_identity` accept them. Both validators can return no reasons, and MAT009 returns `STRUCTURAL_ONLY_UNAUTHENTICATED`. Replacing them with one exact built-in string causes campaign cross-split and source-family leakage reasons. | A textual-equality split theorem does not refine to arbitrary `str` subclasses with inconsistent hashes. No physical evidence is admitted in either result. |
| `dict` subclass whose `.get` raises `RuntimeError` | The MAT008 call propagates that exception before the child scan. | `isinstance(row, dict)` alone does not make the function total. |
| Unhashable `str` subclass used as a row ID | MAT008 `_identity` accepts the text; inserting the ID into `seen_rows` raises `TypeError`. | The direct parent has a dynamic hashability boundary. |
| Exact integer `1` as every `synthetic_fixture` value | The parent's `is True` test does not add `SYNTHETIC_FIXTURE_NOT_PHYSICAL_MEASUREMENT`; otherwise sound self-declared fields return structural-only. | An equivalence with a truthiness-based flag model is false. Physical admission still stays false. |

Exact built-in strings rule out the first and third cases. Exact dictionaries
rule out the overriding `.get` case. Requiring a missing or exact Boolean
`synthetic_fixture` rules out the truthy integer case. A wider domain may be
valid, but needs separate semantic work and tests; the current evidence does
not claim one.

The outer guard itself is deliberately wider than the proposed normal-path
domain: it returns its five-key blocked result for non-lists, empty lists, and
lists longer than 10,000. A `list` subclass can override truthiness, length,
or iteration, so it is not covered by that simple exact-list account merely
because `isinstance(records, list)` is true. A `dict` subclass may similarly
override `.get`. Other custom values can alter equality, hashing, or raise
exceptions. The source contains no general exception handler around the
parent or child scan.

## Operational distinctions a model must retain

MAT008 validates the five source identities before touching its campaign,
phase, run, document, or digest state. MAT009 validates role plus campaign and
lab, then processes the row even if MAT008 rejected its run, document, or row
ID. For example, a missing run on the first train row produces MAT008's
`MISSING_OR_INVALID_SOURCE_IDENTITIES` and
`BOTH_PHASES_REQUIRED_FOR_EACH_CAMPAIGN`, but MAT009 still counts that row's
train phase. It does not add `TRAIN_REQUIRES_BOTH_PHASES`.

Conversely, a row with an undeclared role can be fully processed by MAT008
while MAT009 skips its units, receiver, diagnostic, receipt, and split state.
In the finite case where the skipped row also has bad unit, scale, diagnostic
SHA, and receipt, the only child reasons are
`UNDECLARED_TRAIN_HOLDOUT_ROLE` and `TRAIN_REQUIRES_BOTH_PHASES`. A model that
checks all fields before the role guard would add false reasons.

The child campaign map overwrites the last role for a campaign after recording
a cross-role conflict, while the split sets retain every eligible role. The
diagnostic owner maps instead use `setdefault`, keeping the first
`(campaign, role)` for each valid diagnostic hash or event ID. The source
binder pins this syntax. For exact built-in keys and the current *set-valued*
reason output, a first-owner conflict is present precisely when some later
owner differs from the first. A hypothetical last-owner map would flag an
adjacent transition whenever owners are not all equal, so these two rules
produce the same final presence of each conflict reason. The owner map is not
returned. Finite result tests therefore cannot distinguish this internal
first-owner choice in that exact-key domain; the AST binding records it, and
a refinement proof must follow the source rule rather than infer it from
output alone.

The two diagnostic dimensions are independent. A bad SHA does not enter the
hash owner map, but a valid event ID on the same row still enters the event
owner map. A valid SHA enters its map even if it equals the measurement source
SHA and adds `INDEPENDENT_DIAGNOSTIC_SOURCE_REQUIRED`. Same-campaign,
same-role reuse is accepted by the child ownership gate. A role change within
one campaign can add split leakage without adding cross-campaign diagnostic
reuse. These are structural reason calculations, not verification of real
diagnostic provenance.

## Finite evidence and open work

`tests/test_sonification_formal_mat009_split.py` pins the exact current
MAT009 and MAT008 module SHA-256 values before running independent fabricated
metadata cases. It covers the early result, parent call, campaign cross-split,
lab overlap with three campaigns, both directions of parent/child eligibility
mismatch, parent run/document/byte reasons, independent diagnostic keys,
receipt cardinality, identifier/digest boundaries, subclass and exception
counterexamples, and the exact 14-control ID-to-designated-reason sequence.
It also checks 4,096 four-row exact built-in assignments of role, campaign,
and lab against independent pairwise predicates for the two cross-split reason
IDs. This is finite evidence for those two predicates, not an oracle for every
MAT008 or MAT009 reason.

The tests are finite observations under the current CPython interpreter.
They do not prove all inputs in the exact built-in domain, the selected AST's
semantics, a Lean model refinement, or physical admission. The CPython bridge
and scientific validation remain **OPEN**.
