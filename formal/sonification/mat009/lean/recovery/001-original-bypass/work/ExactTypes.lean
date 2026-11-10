import TypedConsumer

/-!
Independent typed uses of the intended MAT009 model propositions. A theorem
with the same name but a weaker type, such as `True`, cannot satisfy these
consumers. These are statements about eligible-row mathematical models only.
-/

namespace MAT009.ExactTypes
open MAT009

example (parent : ReasonSet) (role : Role)
    (campaign lab reason : String) :
    (initial parent).owner campaign = none ∧
    ¬ (initial parent).campaigns role campaign ∧
    ¬ (initial parent).labs role lab ∧
    ¬ (initial parent).crossed ∧
    ((initial parent).parent reason ↔ parent reason) :=
  M009_R1_initial parent role campaign lab reason

example (s : State) (row : Row) :
    (step s row).owner row.campaign = some row.role ∧
    (∀ key, key ≠ row.campaign → (step s row).owner key = s.owner key) ∧
    (∀ role key,
      (step s row).campaigns role key ↔
        s.campaigns role key ∨ (role = row.role ∧ key = row.campaign)) ∧
    (∀ role key,
      (step s row).labs role key ↔
        s.labs role key ∨ (role = row.role ∧ key = row.lab)) :=
  M009_R2_assignment_overwrite s row

example (s : State) (row : Row) :
    (step s row).crossed ↔
      s.crossed ∨
        ∃ previous : Role,
          s.owner row.campaign = some previous ∧ previous ≠ row.role :=
  M009_R3_cross_role_trigger s row

example (s : State) (row : Row) (role : Role)
    (campaign lab reason : String) :
    (s.campaigns role campaign → (step s row).campaigns role campaign) ∧
    (s.labs role lab → (step s row).labs role lab) ∧
    (s.crossed → (step s row).crossed) ∧
    (familyLeakage s → familyLeakage (step s row)) ∧
    ((step s row).parent reason ↔ s.parent reason) :=
  M009_R4_stickiness s row role campaign lab reason

example (s : State) :
    (finalize s).childReason leakageReason ↔
      (∃ key, s.campaigns .train key ∧ s.campaigns .holdout key) ∨
      (∃ key, s.labs .train key ∧ s.labs .holdout key) :=
  M009_R5_final_set_intersection s

example (s : State) :
    (finalize s).hasReason leakageReason ↔
      s.parent leakageReason ∨ familyLeakage s :=
  M009_R5_parent_union s

example (parent : ReasonSet) (rows : List Row) (role : Role)
    (campaign lab reason : String) :
    ((scan (initial parent) rows).campaigns role campaign ↔
      ∃ row ∈ rows, row.role = role ∧ row.campaign = campaign) ∧
    ((scan (initial parent) rows).labs role lab ↔
      ∃ row ∈ rows, row.role = role ∧ row.lab = lab) ∧
    ((scan (initial parent) rows).parent reason ↔ parent reason) :=
  M009_R6_arbitrary_finite_scan parent rows role campaign lab reason

example (parent : ReasonSet) (rows : List Row) (campaign : String) :
    (scan (initial parent) rows).owner campaign = lastRole rows campaign :=
  M009_R6_latest_owner parent rows campaign

example (parent : ReasonSet) (rows : List Row) :
    (finalize (scan (initial parent) rows)).childReason leakageReason ↔
      (∃ key,
        (∃ row ∈ rows, row.role = .train ∧ row.campaign = key) ∧
        (∃ row ∈ rows, row.role = .holdout ∧ row.campaign = key)) ∨
      (∃ key,
        (∃ row ∈ rows, row.role = .train ∧ row.lab = key) ∧
        (∃ row ∈ rows, row.role = .holdout ∧ row.lab = key)) :=
  M009_R6_final_leakage_iff parent rows

example :
    (∃ rows : List Row,
      (finalize (scan (initial noParent) rows)).status =
        .structuralOnlyUnauthenticated) ∧
    (∃ rows : List Row,
      (finalize (scan (initial noParent) rows)).status =
        .blocked) :=
  M009_R7_nonvacuous

example (registry : MAT009.Diagnostic.Registry)
    (updates : List (String × MAT009.Diagnostic.Owner))
    (key : String) (first : MAT009.Diagnostic.Owner)
    (h : registry key = some first) :
    (MAT009.Diagnostic.scan registry updates) key = some first :=
  MAT009.Diagnostic.scan_first_owner_sticky registry updates key first h

end MAT009.ExactTypes
