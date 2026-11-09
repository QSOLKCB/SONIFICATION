import Std

/- Source-independent model. No claim about Python parsing, mutable dictionaries,
sets, exceptions, or implementation refinement is made by this module. -/
namespace Sonification.Mat008

structure ParsedRow where
  campaign : String
  originalRun : String

structure State where
  owner : String → Option String
  conflict : Bool

def initial : State := ⟨fun _ => none, false⟩

def differentOwner (s : State) (row : ParsedRow) : Bool :=
  match s.owner row.originalRun with
  | none => false
  | some campaign => decide (campaign ≠ row.campaign)

def step (s : State) (row : ParsedRow) : State :=
  ⟨fun key => if key = row.originalRun then some row.campaign else s.owner key,
   s.conflict || differentOwner s row⟩

def scan (rows : List ParsedRow) : State := rows.foldl step initial

def Covers (s : State) (rows : List ParsedRow) : Prop :=
  ∀ row ∈ rows, s.owner row.originalRun = some row.campaign

theorem step_clear_before (s : State) (row : ParsedRow)
    (h : (step s row).conflict = false) : s.conflict = false := by
  simpa only [step, Bool.or_eq_false_iff] using h |>.1

theorem step_clear_same_owner (s : State) (row : ParsedRow) (campaign : String)
    (h : (step s row).conflict = false)
    (ho : s.owner row.originalRun = some campaign) : campaign = row.campaign := by
  have hn : differentOwner s row = false := by
    exact (Bool.or_eq_false_iff.mp h).2
  simp only [differentOwner, ho, decide_eq_false_iff_not] at hn
  exact Classical.not_not.mp hn

theorem step_covers (s : State) (rows : List ParsedRow) (row : ParsedRow)
    (hc : Covers s rows) (hn : (step s row).conflict = false) :
    Covers (step s row) (rows ++ [row]) := by
  intro prior hp
  have hp' : prior ∈ rows ∨ prior = row := by simpa using hp
  cases hp' with
  | inl hprior =>
    have ho := hc prior hprior
    by_cases hr : prior.originalRun = row.originalRun
    · have howner : s.owner row.originalRun = some prior.campaign := by simpa [hr] using ho
      have he := step_clear_same_owner s row prior.campaign hn howner
      simp [step, hr, he]
    · simp [step, hr, ho]
  | inr hprior =>
    subst prior
    simp [step]

theorem scan_append (rows : List ParsedRow) (row : ParsedRow) :
    scan (rows ++ [row]) = step (scan rows) row := by
  simp only [scan, List.foldl_append, List.foldl_cons, List.foldl_nil]

theorem scan_clear_covers (rows : List ParsedRow)
    (hn : (scan rows).conflict = false) : Covers (scan rows) rows := by
  induction rows using List.reverseRecOn with
  | nil =>
    intro row hr
    simp at hr
  | append_singleton rows row ih =>
    rw [scan_append] at hn ⊢
    have hbefore := step_clear_before (scan rows) row hn
    exact step_covers (scan rows) rows row (ih hbefore) hn

theorem reused_run_blocks (rows : List ParsedRow) (a b : ParsedRow)
    (ha : a ∈ rows) (hb : b ∈ rows)
    (hr : a.originalRun = b.originalRun) (hc : a.campaign ≠ b.campaign) :
    (scan rows).conflict = true := by
  cases hflag : (scan rows).conflict with
  | true => rfl
  | false =>
    have covered := scan_clear_covers rows hflag
    have hoa := covered a ha
    have hob := covered b hb
    have he : a.campaign = b.campaign := by
      rw [hr, hob] at hoa
      exact (Option.some.inj hoa).symm
    exact False.elim (hc he)

theorem step_conflict_sticky (s : State) (row : ParsedRow)
    (h : s.conflict = true) : (step s row).conflict = true := by
  simp only [step, h, Bool.true_or]

theorem nonvacuity :
    (scan [⟨"A", "RUN"⟩, ⟨"B", "RUN"⟩, ⟨"B", "OTHER"⟩]).conflict = true ∧
    (scan [⟨"A", "RUN_A"⟩, ⟨"B", "RUN_B"⟩]).conflict = false := by
  decide

end Sonification.Mat008
