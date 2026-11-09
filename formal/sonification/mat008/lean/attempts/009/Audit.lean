import Mat008
import Lean

namespace Mat008StatementChecks
open Sonification.Mat008

def check_step_clear_before (s : State) (row : ParsedRow)
    (h : (step s row).conflict = false) : s.conflict = false := by exact Sonification.Mat008.step_clear_before s row h

def check_step_clear_same_owner (s : State) (row : ParsedRow) (campaign : String)
    (h : (step s row).conflict = false)
    (ho : lookup s.owner row.originalRun = some campaign) : campaign = row.campaign := by exact Sonification.Mat008.step_clear_same_owner s row campaign h ho

def check_step_covers (s : State) (rows : List ParsedRow) (row : ParsedRow)
    (hc : Covers s rows) (hn : (step s row).conflict = false) :
    Covers (step s row) (rows ++ [row]) := by exact Sonification.Mat008.step_covers s rows row hc hn

def check_scan_append (rows : List ParsedRow) (row : ParsedRow) :
    scan (rows ++ [row]) = step (scan rows) row := by exact Sonification.Mat008.scan_append rows row

def check_scan_clear_covers (rows : List ParsedRow)
    (hn : (scan rows).conflict = false) : Covers (scan rows) rows := by exact Sonification.Mat008.scan_clear_covers rows hn

def check_reused_run_blocks (rows : List ParsedRow) (a b : ParsedRow)
    (ha : a ∈ rows) (hb : b ∈ rows)
    (hr : a.originalRun = b.originalRun) (hc : a.campaign ≠ b.campaign) :
    (scan rows).conflict = true := by exact Sonification.Mat008.reused_run_blocks rows a b ha hb hr hc

def check_step_conflict_sticky (s : State) (row : ParsedRow)
    (h : s.conflict = true) : (step s row).conflict = true := by exact Sonification.Mat008.step_conflict_sticky s row h

def check_nonvacuity :
    (scan [⟨"A", "RUN"⟩, ⟨"B", "RUN"⟩, ⟨"B", "OTHER"⟩]).conflict = true ∧
    (scan [⟨"A", "RUN_A"⟩, ⟨"B", "RUN_B"⟩]).conflict = false := by exact Sonification.Mat008.nonvacuity 

end Mat008StatementChecks
open Lean Elab Command

run_cmd do
  let env ← getEnv
  let originModules := #[`Mat008.RunOwnership, `Mat008, env.mainModule]
  for mod in originModules do
    unless mod == env.mainModule || (env.getModuleIdx? mod).isSome do
      throwError "missing required imported module {mod}"
    logInfo m!"SONIFICATION_MODULE {mod}"
  for mod in env.header.moduleNames do
    logInfo m!"SONIFICATION_IMPORT {mod}"
  let allowed := #[`propext, `Quot.sound, `Classical.choice]
  let mut seen : Nat := 0
  let mut theorems : Nat := 0
  for (name, info) in env.checked.get.constants.toList do
    let origin := match env.getModuleIdxFor? name with
      | some idx => env.header.moduleNames[idx.toNat]!
      | none => env.mainModule
    if originModules.contains origin then
      seen := seen + 1
      if info matches .thmInfo _ then
        theorems := theorems + 1
      let axioms ← collectAxioms name
      let unsafeDef := match info with
        | .defnInfo d => d.safety == .unsafe
        | _ => false
      let compilerAux := name.toString.endsWith "_cstage1" || name.toString.endsWith "_cstage2"
      for ax in axioms do
        unless allowed.contains ax || (compilerAux && unsafeDef && #[`lcProof, `lcUnreachable].contains ax) do
          throwError "unapproved transitive axiom {ax} in {name} (origin {origin})"
      if info matches .axiomInfo _ then
        throwError "project axiom declaration {name}"
      let row := Json.mkObj [
        ("origin", toJson origin.toString),
        ("unsafe_definition", toJson unsafeDef),
        ("declaration", toJson name.toString),
        ("kind", toJson (if compilerAux then "compiler_auxiliary" else if info matches .thmInfo _ then "theorem" else "non_theorem")),
        ("type", toJson (← liftTermElabM do pure (← Lean.Meta.ppExpr info.type).pretty)),
        ("axioms", toJson (axioms.map Name.toString))]
      logInfo m!"SONIFICATION_DECL {row.compress}"
  if seen == 0 || theorems == 0 then
    throwError "empty proof inventory"
  logInfo m!"SONIFICATION_AUDIT declarations={seen} theorems={theorems}"

