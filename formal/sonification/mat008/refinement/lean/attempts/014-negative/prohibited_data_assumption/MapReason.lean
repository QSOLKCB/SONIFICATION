import Mat008.RunOwnership

/- Independently defined mathematical dictionary/reason semantics.
These definitions are NOT a semantics or verified translation of CPython.
Noncomputable definitions retain kernel reduction but require no compiled map
implementation; all source-sensitive Python correspondence remains OPEN. -/
noncomputable section
namespace Sonification.Mat008.AbstractPy

abbrev OwnerMap := String → Option String
abbrev ReasonSet := String → Bool

noncomputable def reuseReason : String := "REUSED_ORIGINAL_RUN_ACROSS_CAMPAIGNS"

structure AcceptedRow where
  campaign : String
  originalRun : String

structure PyState where
  owners : OwnerMap
  reasons : ReasonSet

noncomputable def empty : PyState := ⟨fun _ => none, fun _ => false⟩

noncomputable def write (owners : OwnerMap) (key value : String) : OwnerMap :=
  fun query => if query = key then some value else owners query

noncomputable def insert (reasons : ReasonSet) (reason : String) : ReasonSet :=
  fun query => if query = reason then true else reasons query

/- A partial dictionary lookup is modeled by Option. In an actual Python bridge,
membership and short-circuit behavior must separately justify this guard. -/
noncomputable def mismatch (s : PyState) (row : AcceptedRow) : Bool :=
  match s.owners row.originalRun with
  | none => false
  | some oldCampaign => decide (oldCampaign ≠ row.campaign)

noncomputable def pyStep (s : PyState) (row : AcceptedRow) : PyState :=
  let foundMismatch := mismatch s row
  let nextReasons := if foundMismatch then insert s.reasons reuseReason else s.reasons
  ⟨write s.owners row.originalRun row.campaign, nextReasons⟩

noncomputable def pyScanFrom (s : PyState) : List AcceptedRow → PyState
  | [] => s
  | row :: rows => pyScanFrom (pyStep s row) rows

noncomputable def projectRow (row : AcceptedRow) : ParsedRow := ⟨row.campaign, row.originalRun⟩

noncomputable def project (rows : List AcceptedRow) : List ParsedRow := rows.map projectRow

noncomputable def OwnersRelated (owners : OwnerMap) (table : List (String × String)) : Prop :=
  ∀ key, owners key = lookup table key

noncomputable def Related (s : PyState) (m : State) : Prop :=
  OwnersRelated s.owners m.owner ∧ s.reasons reuseReason = m.conflict

/- Explicit instruction semantics for source extraction to target independently.
The extractor-to-instruction correspondence is a separate OPEN obligation. -/
abbrev GateInstruction := Nat

namespace GateInstruction
noncomputable def testExistingOwner : GateInstruction := 0
noncomputable def insertReasonIfMismatch : GateInstruction := 1
noncomputable def overwriteOwner : GateInstruction := 2
end GateInstruction

structure GateFrame where
  state : PyState
  row : AcceptedRow
  mismatchFlag : Bool

noncomputable def executeInstruction (instruction : GateInstruction) (frame : GateFrame) : GateFrame :=
  if instruction = GateInstruction.testExistingOwner then
    { frame with mismatchFlag := mismatch frame.state frame.row }
  else if instruction = GateInstruction.insertReasonIfMismatch then
    if frame.mismatchFlag then
      { frame with state :=
        ⟨frame.state.owners, insert frame.state.reasons reuseReason⟩ }
    else frame
  else if instruction = GateInstruction.overwriteOwner then
    { frame with state :=
      ⟨write frame.state.owners frame.row.originalRun frame.row.campaign,
       frame.state.reasons⟩ }
  else frame

noncomputable def executeInstructions (frame : GateFrame) : List GateInstruction → GateFrame
  | [] => frame
  | instruction :: instructions =>
      executeInstructions (executeInstruction instruction frame) instructions

noncomputable def runGateProgram : List GateInstruction :=
  [GateInstruction.testExistingOwner, GateInstruction.insertReasonIfMismatch,
    GateInstruction.overwriteOwner]

theorem instruction_program_correspondence (s : PyState) (row : AcceptedRow)
    (arbitraryPriorFlag : Bool) :
    (executeInstructions ⟨s, row, arbitraryPriorFlag⟩ runGateProgram).state = pyStep s row := by
  cases hg : mismatch s row <;>
    simp [executeInstructions, executeInstruction, runGateProgram,
      GateInstruction.testExistingOwner, GateInstruction.insertReasonIfMismatch,
      GateInstruction.overwriteOwner, pyStep, hg]

noncomputable def FiniteSupport (owners : OwnerMap) : Prop :=
  ∃ keys : List String, ∀ key, owners key ≠ none → key ∈ keys

theorem lookup_support (table : List (String × String)) (key : String)
    (h : lookup table key ≠ none) : key ∈ table.map Prod.fst := by
  induction table with
  | nil => exact False.elim (h rfl)
  | cons pair rest ih =>
    rcases pair with ⟨run, campaign⟩
    by_cases hk : key = run
    · simp [hk]
    · have hrest : lookup rest key ≠ none := by simpa [lookup, hk] using h
      exact List.mem_cons.mpr (Or.inr (ih hrest))

theorem r2_finite_support (s : PyState) (m : State) (h : Related s m) :
    FiniteSupport s.owners := by
  refine ⟨m.owner.map Prod.fst, ?_⟩
  intro key hk
  apply lookup_support m.owner key
  simpa only [← h.1 key] using hk

theorem r1_empty_related : Related empty initial := by
  constructor
  · intro key
    rfl
  · rfl

/- R2 is conditional on the explicit representation relation. It does not assert
that any CPython dictionary has been proved to implement OwnerMap. -/
theorem r2_lookup (s : PyState) (m : State) (h : Related s m) (key : String) :
    s.owners key = lookup m.owner key := by
  exact h.1 key

theorem write_same (owners : OwnerMap) (key value : String) :
    write owners key value key = some value := by
  simp [write]

theorem write_other (owners : OwnerMap) (key value query : String) (h : query ≠ key) :
    write owners key value query = owners query := by
  simp only [write, if_neg h]

theorem write_related (owners : OwnerMap) (table : List (String × String))
    (key value : String) (h : OwnersRelated owners table) :
    OwnersRelated (write owners key value) ((key, value) :: table) := by
  intro query
  simp only [write, lookup]
  split
  · rfl
  · exact h query

theorem r3_overwrite (s : PyState) (m : State) (row : AcceptedRow)
    (h : Related s m) :
    OwnersRelated (pyStep s row).owners (step m (projectRow row)).owner := by
  exact write_related s.owners m.owner row.originalRun row.campaign h.1

theorem r3_latest_campaign (s : PyState) (row : AcceptedRow) :
    (pyStep s row).owners row.originalRun = some row.campaign := by
  simp [pyStep, write]

theorem mismatch_related (s : PyState) (m : State) (row : AcceptedRow)
    (h : Related s m) : mismatch s row = differentOwner m (projectRow row) := by
  simp only [mismatch, differentOwner, projectRow, h.1 row.originalRun]
  rfl

theorem mismatch_iff (s : PyState) (row : AcceptedRow) :
    mismatch s row = true ↔
      ∃ oldCampaign, s.owners row.originalRun = some oldCampaign ∧
        oldCampaign ≠ row.campaign := by
  cases ho : s.owners row.originalRun with
  | none => simp [mismatch, ho]
  | some oldCampaign => simp [mismatch, ho]

theorem reason_step (s : PyState) (row : AcceptedRow) :
    (pyStep s row).reasons reuseReason =
      (s.reasons reuseReason || mismatch s row) := by
  unfold pyStep
  cases hg : mismatch s row <;> simp [insert, hg]

theorem step_related (s : PyState) (m : State) (row : AcceptedRow)
    (h : Related s m) : Related (pyStep s row) (step m (projectRow row)) := by
  constructor
  · exact r3_overwrite s m row h
  · rw [reason_step, h.2, mismatch_related s m row h]
    rfl

theorem r4_reason_iff (s : PyState) (m : State) (row : AcceptedRow)
    (h : Related s m) :
    (pyStep s row).reasons reuseReason = true ↔
      (step m (projectRow row)).conflict = true := by
  rw [(step_related s m row h).2]

theorem new_reason_iff_mismatch (s : PyState) (row : AcceptedRow)
    (h : s.reasons reuseReason = false) :
    (pyStep s row).reasons reuseReason = true ↔ mismatch s row = true := by
  rw [reason_step, h]
  simp only [Bool.false_or]

theorem r5_reason_sticky (s : PyState) (row : AcceptedRow)
    (h : s.reasons reuseReason = true) :
    (pyStep s row).reasons reuseReason = true := by
  rw [reason_step, h]
  simp only [Bool.true_or]

theorem r5_sequence_sticky (s : PyState) (rows : List AcceptedRow)
    (h : s.reasons reuseReason = true) :
    (pyScanFrom s rows).reasons reuseReason = true := by
  induction rows generalizing s with
  | nil => exact h
  | cons row rows ih => exact ih (pyStep s row) (r5_reason_sticky s row h)

theorem reason_frame (s : PyState) (row : AcceptedRow) (reason : String)
    (h : reason ≠ reuseReason) :
    (pyStep s row).reasons reason = s.reasons reason := by
  unfold pyStep
  cases hg : mismatch s row <;> simp [insert, hg, h]

theorem r6_sequence_related (s : PyState) (m : State) (rows : List AcceptedRow)
    (h : Related s m) :
    Related (pyScanFrom s rows) (scanFrom m (project rows)) := by
  induction rows generalizing s m with
  | nil => exact h
  | cons row rows ih =>
    exact ih (pyStep s row) (step m (projectRow row)) (step_related s m row h)

/- This projection's None events are mathematical skip events, not parsed raw
Python rows. Actual failed-parse frames must be independently established. -/
noncomputable def acceptedProjection : List (Option AcceptedRow) → List AcceptedRow
  | [] => []
  | none :: events => acceptedProjection events
  | some row :: events => row :: acceptedProjection events

noncomputable def eventScanFrom (s : PyState) : List (Option AcceptedRow) → PyState
  | [] => s
  | none :: events => eventScanFrom s events
  | some row :: events => eventScanFrom (pyStep s row) events

theorem event_projection (s : PyState) (events : List (Option AcceptedRow)) :
    eventScanFrom s events = pyScanFrom s (acceptedProjection events) := by
  induction events generalizing s with
  | nil => rfl
  | cons event events ih =>
    cases event with
    | none => exact ih s
    | some row => exact ih (pyStep s row)

theorem r6_accepted_projection (s : PyState) (m : State)
    (events : List (Option AcceptedRow)) (h : Related s m) :
    Related (eventScanFrom s events) (scanFrom m (project (acceptedProjection events))) := by
  rw [event_projection]
  exact r6_sequence_related s m (acceptedProjection events) h

theorem skip_frame (before after : PyState) (m : State)
    (h : Related before m)
    (howners : ∀ key, after.owners key = before.owners key)
    (hreason : after.reasons reuseReason = before.reasons reuseReason) :
    Related after m := by
  constructor
  · intro key
    rw [howners, h.1 key]
  · rw [hreason, h.2]

theorem r7_collision_reason (rows : List AcceptedRow) (a b : AcceptedRow)
    (ha : a ∈ rows) (hb : b ∈ rows)
    (hr : a.originalRun = b.originalRun) (hc : a.campaign ≠ b.campaign) :
    (pyScanFrom empty rows).reasons reuseReason = true := by
  have hrep := r6_sequence_related empty initial rows r1_empty_related
  have hma : projectRow a ∈ project rows := List.mem_map.mpr ⟨a, ha, rfl⟩
  have hmb : projectRow b ∈ project rows := List.mem_map.mpr ⟨b, hb, rfl⟩
  have hcollision := reused_run_blocks (project rows) (projectRow a) (projectRow b)
    hma hmb hr hc
  rw [hrep.2]
  exact hcollision

theorem preexisting_reason_counterexample :
    let s : PyState := ⟨fun _ => none, fun _ => true⟩
    mismatch s ⟨"CAMPAIGN", "RUN"⟩ = false ∧
    (pyStep s ⟨"CAMPAIGN", "RUN"⟩).reasons reuseReason = true := by
  exact ⟨rfl, rfl⟩

theorem nonvacuity :
    (pyScanFrom empty [⟨"A", "RUN"⟩, ⟨"B", "RUN"⟩, ⟨"B", "OTHER"⟩]).reasons reuseReason = true ∧
    (pyScanFrom empty [⟨"A", "RUN_A"⟩, ⟨"B", "RUN_B"⟩]).reasons reuseReason = false := by
  decide

noncomputable def prohibitedData : Nat := by sorry

end Sonification.Mat008.AbstractPy
