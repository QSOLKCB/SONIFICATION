# Initial mathematical specification

This independently authored specification concerns a new mathematical model.
Production reference: `mat-spec-007-v0.1.0`, peeled commit
`b97348ff8fcf3f57764dec21a8914f153f96a745`, source tree
`c1b842c6bace3ccb01714007b8d7ebb05bcecd31`,
`materials/mat_spec_007.py` SHA-256
`2e363adea6c781ab68aec69d2ee5c7d712fc5e46346ae5be21d8cf3e929781c6`.
The model's relationship to production `classify`, `interval`, and `pairwise_fits`
is an OPEN refinement obligation. A string-returning Python function, exception
semantics, `fractions.Fraction`, decimal parsing, and row processing are absent
from this model.

## Integer interval contract

An interval is a pair of arbitrary mathematical integers `(lo, hi)`. Validity is
`lo ≤ hi`. The classifier returns no relation if either interval is invalid;
otherwise it returns `below` if `a.hi < b.lo`, `above` if `b.hi < a.lo`, and
`overlap` otherwise. Endpoint contact counts as overlap. Rejection is represented
by `Option.none`; this is a mathematical observable, not a proved representation
of a Python exception. A box is `(center - error, center + error)`. Scaling
multiplies every endpoint by the same integer.

The following are universally quantified, with no finite endpoint bounds:

| Declaration under `Sonification` | Exact scope |
| --- | --- |
| `invalid_iff` | For every pair, rejection iff at least one is invalid. |
| `below_iff` | For every pair, below iff both valid and `a.hi < b.lo`. |
| `above_iff` | For every pair, above iff both valid and `b.hi < a.lo`. |
| `overlap_iff` | For every pair, overlap iff both valid and `a.lo ≤ b.hi` and `b.lo ≤ a.hi`. |
| `exhaustive` | Every pair of valid intervals has one of the three relations. |
| `exclusive` | For valid intervals, no two of the three endpoint predicates hold together. |
| `reversal` | For every pair, swapping arguments reverses below/above and preserves overlap or rejection. |
| `scale_lt_iff` | For every `k,x,y : Int`, if `0 < k`, then `k*x < k*y` iff `x < y`. |
| `positive_scale` | For every pair and `k > 0`, scaling preserves the complete classifier result, including invalidity. |
| `box_valid` | For every integer center and error, error ≥ 0 implies ordered box endpoints. |
| `touching` | Valid intervals with `a.hi = b.lo` overlap. |
| `inhabited_branches` | Four explicit examples exercise below, above, touching overlap, and invalid rejection. |

The exact binder types and propositions are retained in `lean/theorem-statements.json`,
`lean/Sonification/Intervals.lean`, and the independently fixed typed consumers
in `lean/Audit.lean`. Changing a theorem to a weaker proposition must fail its
consumer. Consumers are never regenerated during verification.

## Abstract strict-comparison contract

`Sonification.Ordered.OrderSpec α` contains a decidable relation `lt`,
irreflexivity, transitivity, and the compatibility law
`lt x y → ¬lt z y → lt x z`. These are explicit structure fields, not global
axiom declarations. They hold for integer strict comparison; a constructed
`integerOrder` supplies proofs. This is a strict comparison abstraction; equality
of distinct representations and rational normalization are outside it.

Its interval validity is `¬lt hi lo`. Seven named theorems establish:

| Declaration under `Sonification.Ordered` | Exact scope |
| --- | --- |
| `separation_exclusive` | Every order contract and valid pair forbids simultaneous separation in both directions. |
| `asymmetric` | Every order contract has asymmetric strict comparison. |
| `classify_below_iff` | For every pair, below iff both valid and strictly separated in the below direction. |
| `classify_overlap_iff` | For every pair, overlap iff both valid and neither strict separation holds. |
| `exhaustive` | Every valid pair has a relation. |
| `order_reflecting_map` | For every source and target order contract, and every function reflecting and preserving strict comparison for all endpoint values, mapping endpoints preserves classifier output. |
| `integer_specialization` | For every integer interval pair, the generic classifier instantiated with integer comparison equals the integer classifier after a constructor mapping. |

The map theorem is conditional on the explicit universal comparison equivalence.
It is not a proof that an arbitrary conversion, rational implementation, or
Python operation has this property. No core `Std.Internal.Rat` semantics are
assumed. A rational instantiation and a CPython Fraction bridge remain OPEN.

## Trust, coverage, and non-vacuity

The effective tool is Lean 4.19.0, release commit `6caaee842e94`, with only its
bundled `Std`, `Init`, and Lean metaprogram libraries. The runner records the actual
executable digest and the SHA-256 of every imported toolchain `.olean` module.
The installed distribution, Lean kernel, compiler/elaborator, OS execution,
Python audit runner, and provenance of installed binaries remain trusted.
There is no independently checked proof of this audit runner or compiler.

The audit inspects originating modules, not namespace prefixes, and collects
transitive axioms before considering whether a declaration is proposition-valued.
This includes safe data helpers, generated declarations, and typed consumers in
`Audit`. Expected module and declaration inventories must match exactly; every
expected module is compiled explicitly in a fresh temporary directory.

The permitted logical axioms are `propext` (propositional extensionality),
`Quot.sound` (quotient soundness), and `Classical.choice` (classical selection).
Per-declaration lists are recorded. There are no project axioms or `sorryAx`
dependencies in the successful build. No native evaluation is used to justify
any theorem. `omega` produces proofs checked by the kernel.

The installed Lean compiler also exports unsafe `_cstage1`/`_cstage2` auxiliary
declarations. The successful audit reports these separately, including their
`lcProof` and `lcUnreachable` compiler-only assumptions. These are permitted only
on unsafe definitions with those exact generated suffixes. They are prohibited
in every safe helper and theorem. This compiler machinery is part of the trusted
toolchain, not an extra mathematical premise. The runner's module inventory and
baseline input comparison must prevent an unaudited module from entering the
proof. An independently reviewed baseline remains necessary: changing both a
proof and its expected inventory without external comparison cannot authenticate
its original statement.

The concrete branch examples and the integer instance witness satisfiable
preconditions. All valid-interval assumptions are explicit. There is no claim
that `pairwise_fits` inputs satisfy them, that CSV parsing supplies those inputs,
or that any proved ordering establishes scientific evidence admission.

No scientific or physical results follow from these models. MAT-SPEC closure
remains `NUMBERED_SERIES_CLOSED_AT_010_WITH_OPEN_SCIENTIFIC_GATES`.
