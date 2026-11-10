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
  let nextReasons := if foundMismatch then insert s.reasons reuseReason else (fun _ => false)
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


 theorem erasure_counterexample :
     let s : PyState := ⟨fun _ => none, fun _ => true⟩
     (pyStep s ⟨"C", "R"⟩).reasons reuseReason = false := by rfl
 end Sonification.Mat008.AbstractPy
