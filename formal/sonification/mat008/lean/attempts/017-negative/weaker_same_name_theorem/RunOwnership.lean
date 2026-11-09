import Std

/- Source-independent model. No claim about Python parsing, mutable dictionaries,
sets, exceptions, or implementation refinement is made by this module. -/
namespace Sonification.Mat008

structure ParsedRow where
  campaign : String
  originalRun : String

structure State where
  owner : List (String × String)
  conflict : Bool

def lookup : List (String × String) → String → Option String
  | [], _ => none
  | (run, campaign) :: rest, key => if key = run then some campaign else lookup rest key

def initial : State := ⟨[], false⟩

def differentOwner (s : State) (row : ParsedRow) : Bool :=
  match lookup s.owner row.originalRun with
  | none => false
  | some campaign => decide (campaign ≠ row.campaign)

def step (s : State) (row : ParsedRow) : State :=
  ⟨(row.originalRun, row.campaign) :: s.owner,
   s.conflict || differentOwner s row⟩

def scanFrom (s : State) : List ParsedRow → State
  | [] => s
  | row :: rows => scanFrom (step s row) rows

def scan (rows : List ParsedRow) : State := scanFrom initial rows

def Covers (s : State) (rows : List ParsedRow) : Prop :=
  ∀ row ∈ rows, lookup s.owner row.originalRun = some row.campaign

theorem step_clear_before (s : State) (row : ParsedRow)
    (h : (step s row).conflict = false) : s.conflict = false := by
  exact (Bool.or_eq_false_iff.mp h).1

theorem step_clear_same_owner (s : State) (row : ParsedRow) (campaign : String)
    (h : (step s row).conflict = false)
    (ho : lookup s.owner row.originalRun = some campaign) : campaign = row.campaign := by
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
    · have howner : lookup s.owner row.originalRun = some prior.campaign := by simpa [hr] using ho
      have he := step_clear_same_owner s row prior.campaign hn howner
      simp [step, lookup, hr, he]
    · simp [step, lookup, hr, ho]
  | inr hprior =>
    subst prior
    simp [step, lookup]

theorem scanFrom_append (s : State) (xs ys : List ParsedRow) :
    scanFrom s (xs ++ ys) = scanFrom (scanFrom s xs) ys := by
  induction xs generalizing s with
  | nil => rfl
  | cons row rows ih => exact ih (step s row)

theorem scan_append (rows : List ParsedRow) (row : ParsedRow) :
    scan (rows ++ [row]) = step (scan rows) row := by
  simp only [scan, scanFrom_append, scanFrom]

theorem snoc_induction {α : Type} (motive : List α → Prop)
    (nil : motive [])
    (append_singleton : ∀ rows row, motive rows → motive (rows ++ [row])) :
    ∀ rows, motive rows := by
  have aux : ∀ reversed : List α, motive reversed.reverse := by
    intro reversed
    induction reversed with
    | nil => exact nil
    | cons row rows ih =>
      simpa only [List.reverse_cons] using append_singleton rows.reverse row ih
  intro rows
  simpa only [List.reverse_reverse] using aux rows.reverse

theorem scan_clear_covers (rows : List ParsedRow)
    (hn : (scan rows).conflict = false) : Covers (scan rows) rows := by
  induction rows using snoc_induction with
  | nil =>
    intro row hr
    simp at hr
  | append_singleton rows row ih =>
    rw [scan_append] at hn ⊢
    have hbefore := step_clear_before (scan rows) row hn
    exact step_covers (scan rows) rows row (ih hbefore) hn

theorem reused_run_blocks : True := by trivial

theorem step_conflict_sticky (s : State) (row : ParsedRow)
    (h : s.conflict = true) : (step s row).conflict = true := by
  simp only [step, h, Bool.true_or]

theorem nonvacuity :
    (scan [⟨"A", "RUN"⟩, ⟨"B", "RUN"⟩, ⟨"B", "OTHER"⟩]).conflict = true ∧
    (scan [⟨"A", "RUN_A"⟩, ⟨"B", "RUN_B"⟩]).conflict = false := by
  decide

end Sonification.Mat008
