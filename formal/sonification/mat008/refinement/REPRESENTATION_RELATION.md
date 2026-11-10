# Run-owner state representation relation

The accepted Lean state stores `owner : List (String × String)` newest first
and `conflict : Bool`. `lookup owner key` returns the campaign from the first
matching pair. Repeated keys therefore retain earlier historical pairs but
only the newest one is observable.

The new abstract Python state observes a mutable dictionary through a total
function `D : String → Option String`, where `none` means absent. It observes
the reason set through a Boolean `B`, where `B = true` means the exact
`REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS` reason is present. The relation is:

```text
Rel(D, B, s)  iff
  (for every string k, D(k) = lookup(s.owner, k))
  and B = s.conflict.
```

The relation is **extensional**. It does not assert that CPython's dictionary
has the same internal order, capacity or hash-table layout as Lean's list.
The owner overwrite `D[run] := campaign` is represented by the pointwise
function `D'(k) = some campaign` when `k = run`, and `D'(k) = D(k)` otherwise.
The Lean step prepends `(run, campaign)` to its owner list. Those updates
agree under `Rel` for every key, including a repeated run whose earlier list
pairs are shadowed. This is the central owner-update obligation.

The abstract mismatch predicate is true exactly when the old observation
`D(run)` is `some old_campaign` with `old_campaign ≠ campaign`. A missing key
does not evaluate a value comparison in the frozen source. The abstract reason
update is `B' = B ∨ mismatch`. It cannot clear a prior conflict. The Lean
`step` uses the same Boolean recurrence through `differentOwner`. This
establishes the intended reason-bit correspondence within the **abstract**
semantics; actual CPython execution is a distinct obligation.

For a finite ordered list `xs` of processed `ParsedRow` values, the abstract
fold applies the update in list order. The Lean side applies `scanFrom s xs`.
Induction on `xs` gives sequence correspondence if the initial states relate
and each step preserves `Rel`. Order matters to the final owner map. The
existence of any cross-campaign shared run forces the sticky conflict flag in
the accepted model regardless of where that pair appears in the finite list.
No claim is made that the complete validator output is permutation invariant.

The raw-to-processed projection is defined by the frozen control-flow prefix:
iterate the supplied records in order; discard a non-dict row and any row
where one of five ordered `_identity` calls raises a caught `ValueError`;
retain every row reaching the ownership gate. Later-invalid measurements and
duplicate row IDs remain in this sequence. The relation from actual Python
records to Lean strings requires exact built-in identity values or a separately
proved hash/equality representation. The current production caller does not
guarantee that premise.

At normal nonempty return, a final observation bridge would show:

```text
"REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS" in report["reasons"]
    iff B_final = true.
```

The source returns `sorted(reasons)` and contains only `reasons.add` accesses,
but the observation bridge is not yet a Lean theorem about actual Python
execution. A subclass with equal text but inconsistent hashes, or a campaign
subclass overriding `__ne__`, breaks the unrestricted textual interpretation.
The known counterexamples are retained in `PYTHON_SEMANTICS.json` and the
focused tests. `REFINEMENT_PROVED` remains **OPEN**.
