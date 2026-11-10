import ArchiveConsumer
import Lean

/-!
Inspect every declaration originating in the MAT010 proof modules, including
compiler-created declarations. The Python checker binds this report to the
source commit and checks its complete inventory and imported module hashes.
Names resembling compiler output receive no special trust.
-/

open Lean Elab Command

run_cmd do
  let env ← getEnv
  let origins := #[`ArchiveModel, `ArchiveConsumer, env.mainModule]
  for mod in origins do
    unless mod == env.mainModule || (env.getModuleIdx? mod).isSome do
      throwError "missing required imported module {mod}"
    logInfo m!"MAT010_MODULE {mod}"
  for mod in env.header.moduleNames do
    logInfo m!"MAT010_IMPORT {mod}"
  let allowedLogical := #[`propext, `Quot.sound, `Classical.choice]
  let mut seen : Nat := 0
  let mut theorems : Nat := 0
  let declarations := env.checked.get.constants.toList.mergeSort fun a b =>
    decide (a.1.toString ≤ b.1.toString)
  for (name, info) in declarations do
    let origin := match env.getModuleIdxFor? name with
      | some idx => env.header.moduleNames[idx.toNat]!
      | none => env.mainModule
    if origins.contains origin then
      seen := seen + 1
      if info matches .thmInfo _ then
        theorems := theorems + 1
      let unsafeDef : Bool := match info with
        | .defnInfo d => d.safety == DefinitionSafety.unsafe
        | _ => false
      let unsafeAxiom : Bool := match info with
        | .axiomInfo a => a.isUnsafe
        | _ => false
      let hasSourceRange := (← findDeclarationRangesCore? name).isSome
      let typeStr ← liftTermElabM do
        pure (← Lean.Meta.ppExpr info.type).pretty
      if info matches .axiomInfo _ then
        throwError "project axiom declaration {name}"
      if unsafeDef then
        throwError "unsafe project definition {name}"
      let axioms ← collectAxioms name
      for ax in axioms do
        unless allowedLogical.contains ax do
          throwError "unapproved transitive axiom {ax} in {name} (origin {origin})"
      let row := Json.mkObj [
        ("origin", toJson origin.toString),
        ("declaration", toJson name.toString),
        ("kind", toJson (if info matches .thmInfo _ then "theorem" else "non_theorem")),
        ("is_axiom", toJson (info matches .axiomInfo _)),
        ("unsafe_axiom", toJson unsafeAxiom),
        ("unsafe_definition", toJson unsafeDef),
        ("has_source_range", toJson hasSourceRange),
        ("type", toJson typeStr),
        ("axioms", toJson (axioms.map Name.toString))]
      logInfo m!"MAT010_DECL {row.compress}"
  if seen == 0 || theorems < 7 then
    throwError "incomplete proof inventory"
  logInfo m!"MAT010_AUDIT declarations={seen} theorems={theorems}"
