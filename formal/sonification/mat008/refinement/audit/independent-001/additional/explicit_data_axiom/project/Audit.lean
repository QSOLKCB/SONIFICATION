import Refine
import Lean

noncomputable section
namespace RefineStatementChecks
open Sonification.Mat008 Sonification.Mat008.AbstractPy

noncomputable def check_instruction_program_correspondence (s : PyState) (row : AcceptedRow)
    (arbitraryPriorFlag : Bool) :
    (executeInstructions ⟨s, row, arbitraryPriorFlag⟩ runGateProgram).state = pyStep s row := by
  exact Sonification.Mat008.AbstractPy.instruction_program_correspondence s row arbitraryPriorFlag

noncomputable def check_lookup_support (table : List (String × String)) (key : String)
    (h : lookup table key ≠ none) : key ∈ table.map Prod.fst := by
  exact Sonification.Mat008.AbstractPy.lookup_support table key h

noncomputable def check_r2_finite_support (s : PyState) (m : State) (h : Related s m) :
    FiniteSupport s.owners := by
  exact Sonification.Mat008.AbstractPy.r2_finite_support s m h

noncomputable def check_r1_empty_related : Related empty initial := by
  exact Sonification.Mat008.AbstractPy.r1_empty_related

noncomputable def check_r2_lookup (s : PyState) (m : State) (h : Related s m) (key : String) :
    s.owners key = lookup m.owner key := by
  exact Sonification.Mat008.AbstractPy.r2_lookup s m h key

noncomputable def check_write_same (owners : OwnerMap) (key value : String) :
    write owners key value key = some value := by
  exact Sonification.Mat008.AbstractPy.write_same owners key value

noncomputable def check_write_other (owners : OwnerMap) (key value query : String) (h : query ≠ key) :
    write owners key value query = owners query := by
  exact Sonification.Mat008.AbstractPy.write_other owners key value query h

noncomputable def check_write_related (owners : OwnerMap) (table : List (String × String))
    (key value : String) (h : OwnersRelated owners table) :
    OwnersRelated (write owners key value) ((key, value) :: table) := by
  exact Sonification.Mat008.AbstractPy.write_related owners table key value h

noncomputable def check_r3_overwrite (s : PyState) (m : State) (row : AcceptedRow)
    (h : Related s m) :
    OwnersRelated (pyStep s row).owners (step m (projectRow row)).owner := by
  exact Sonification.Mat008.AbstractPy.r3_overwrite s m row h

noncomputable def check_r3_latest_campaign (s : PyState) (row : AcceptedRow) :
    (pyStep s row).owners row.originalRun = some row.campaign := by
  exact Sonification.Mat008.AbstractPy.r3_latest_campaign s row

noncomputable def check_mismatch_related (s : PyState) (m : State) (row : AcceptedRow)
    (h : Related s m) : mismatch s row = differentOwner m (projectRow row) := by
  exact Sonification.Mat008.AbstractPy.mismatch_related s m row h

noncomputable def check_mismatch_iff (s : PyState) (row : AcceptedRow) :
    mismatch s row = true ↔
      ∃ oldCampaign, s.owners row.originalRun = some oldCampaign ∧
        oldCampaign ≠ row.campaign := by
  exact Sonification.Mat008.AbstractPy.mismatch_iff s row

noncomputable def check_reason_step (s : PyState) (row : AcceptedRow) :
    (pyStep s row).reasons reuseReason =
      (s.reasons reuseReason || mismatch s row) := by
  exact Sonification.Mat008.AbstractPy.reason_step s row

noncomputable def check_step_related (s : PyState) (m : State) (row : AcceptedRow)
    (h : Related s m) : Related (pyStep s row) (step m (projectRow row)) := by
  exact Sonification.Mat008.AbstractPy.step_related s m row h

noncomputable def check_r4_reason_iff (s : PyState) (m : State) (row : AcceptedRow)
    (h : Related s m) :
    (pyStep s row).reasons reuseReason = true ↔
      (step m (projectRow row)).conflict = true := by
  exact Sonification.Mat008.AbstractPy.r4_reason_iff s m row h

noncomputable def check_new_reason_iff_mismatch (s : PyState) (row : AcceptedRow)
    (h : s.reasons reuseReason = false) :
    (pyStep s row).reasons reuseReason = true ↔ mismatch s row = true := by
  exact Sonification.Mat008.AbstractPy.new_reason_iff_mismatch s row h

noncomputable def check_r5_reason_sticky (s : PyState) (row : AcceptedRow)
    (h : s.reasons reuseReason = true) :
    (pyStep s row).reasons reuseReason = true := by
  exact Sonification.Mat008.AbstractPy.r5_reason_sticky s row h

noncomputable def check_r5_sequence_sticky (s : PyState) (rows : List AcceptedRow)
    (h : s.reasons reuseReason = true) :
    (pyScanFrom s rows).reasons reuseReason = true := by
  exact Sonification.Mat008.AbstractPy.r5_sequence_sticky s rows h

noncomputable def check_reason_frame (s : PyState) (row : AcceptedRow) (reason : String)
    (h : reason ≠ reuseReason) :
    (pyStep s row).reasons reason = s.reasons reason := by
  exact Sonification.Mat008.AbstractPy.reason_frame s row reason h

noncomputable def check_r6_sequence_related (s : PyState) (m : State) (rows : List AcceptedRow)
    (h : Related s m) :
    Related (pyScanFrom s rows) (scanFrom m (project rows)) := by
  exact Sonification.Mat008.AbstractPy.r6_sequence_related s m rows h

noncomputable def check_event_projection (s : PyState) (events : List (Option AcceptedRow)) :
    eventScanFrom s events = pyScanFrom s (acceptedProjection events) := by
  exact Sonification.Mat008.AbstractPy.event_projection s events

noncomputable def check_r6_accepted_projection (s : PyState) (m : State)
    (events : List (Option AcceptedRow)) (h : Related s m) :
    Related (eventScanFrom s events) (scanFrom m (project (acceptedProjection events))) := by
  exact Sonification.Mat008.AbstractPy.r6_accepted_projection s m events h

noncomputable def check_skip_frame (before after : PyState) (m : State)
    (h : Related before m)
    (howners : ∀ key, after.owners key = before.owners key)
    (hreason : after.reasons reuseReason = before.reasons reuseReason) :
    Related after m := by
  exact Sonification.Mat008.AbstractPy.skip_frame before after m h howners hreason

noncomputable def check_r7_collision_reason (rows : List AcceptedRow) (a b : AcceptedRow)
    (ha : a ∈ rows) (hb : b ∈ rows)
    (hr : a.originalRun = b.originalRun) (hc : a.campaign ≠ b.campaign) :
    (pyScanFrom empty rows).reasons reuseReason = true := by
  exact Sonification.Mat008.AbstractPy.r7_collision_reason rows a b ha hb hr hc

noncomputable def check_preexisting_reason_counterexample :
    let s : PyState := ⟨fun _ => none, fun _ => true⟩
    mismatch s ⟨"CAMPAIGN", "RUN"⟩ = false ∧
    (pyStep s ⟨"CAMPAIGN", "RUN"⟩).reasons reuseReason = true := by
  exact Sonification.Mat008.AbstractPy.preexisting_reason_counterexample

noncomputable def check_nonvacuity :
    (pyScanFrom empty [⟨"A", "RUN"⟩, ⟨"B", "RUN"⟩, ⟨"B", "OTHER"⟩]).reasons reuseReason = true ∧
    (pyScanFrom empty [⟨"A", "RUN_A"⟩, ⟨"B", "RUN_B"⟩]).reasons reuseReason = false := by
  exact Sonification.Mat008.AbstractPy.nonvacuity

end RefineStatementChecks

open Lean Elab Command

run_cmd do
  let env ← getEnv
  let originModules := #[`Mat008.RunOwnership, `Refine.MapReason, `Refine, env.mainModule]
  for mod in originModules do
    unless mod == env.mainModule || (env.getModuleIdx? mod).isSome do
      throwError "missing required imported module {mod}"
    logInfo m!"MAT008_REFINE_MODULE {mod}"
  for mod in env.header.moduleNames do
    logInfo m!"MAT008_REFINE_IMPORT {mod}"
  let allowed := #[`propext, `Quot.sound, `Classical.choice]
  let declarations := env.checked.get.constants.toList.filter fun entry =>
    let origin : Name := match env.getModuleIdxFor? entry.1 with
      | some idx => env.header.moduleNames[idx.toNat]!
      | none => env.mainModule
    originModules.contains origin
  let orderedDeclarations := declarations.mergeSort fun a b =>
    let aUnsafe := match a.2 with
      | .defnInfo d => d.safety == DefinitionSafety.unsafe
      | _ => false
    let bUnsafe := match b.2 with
      | .defnInfo d => d.safety == DefinitionSafety.unsafe
      | _ => false
    if aUnsafe != bUnsafe then !aUnsafe else decide (a.1.toString ≤ b.1.toString)
  let mut seen : Nat := 0
  let mut theoremCount : Nat := 0
  for (name, info) in orderedDeclarations do
    let origin : Name := match env.getModuleIdxFor? name with
      | some idx => env.header.moduleNames[idx.toNat]!
      | none => env.mainModule
    seen := seen + 1
    if info matches .thmInfo _ then theoremCount := theoremCount + 1
    let axioms ← collectAxioms name
    for ax in axioms do
      unless allowed.contains ax do
        throwError "unapproved transitive axiom {ax} in {name} (origin {origin})"
    if info matches .axiomInfo _ then throwError "project axiom declaration {name}"
    let unsafeDefinition : Bool := match info with
      | .defnInfo d => d.safety == DefinitionSafety.unsafe
      | _ => false
    let row := Json.mkObj [
      ("origin", toJson (Name.toString origin)),
      ("declaration", toJson (Name.toString name)),
      ("unsafe_definition", toJson unsafeDefinition),
      ("kind", toJson (if info matches .thmInfo _ then "theorem" else "non_theorem")),
      ("type", toJson (← liftTermElabM do pure (← Lean.Meta.ppExpr info.type).pretty)),
      ("axioms", toJson (axioms.map Name.toString))]
    logInfo m!"MAT008_REFINE_DECL {row.compress}"
  if seen == 0 || theoremCount == 0 then throwError "empty proof inventory"
  logInfo m!"MAT008_REFINE_AUDIT declarations={seen} theorems={theoremCount}"
