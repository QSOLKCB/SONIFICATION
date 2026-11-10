import ExactTypes
import Lean

/-!
Enumerate every declaration whose origin is a MAT009 proof module, including
helpers and typed consumers. The script that runs this module checks the
inventory. `collectAxioms` traverses each declaration's logical dependencies.
-/

open Lean Elab Command

run_cmd do
  let env ← getEnv
  let origins := #[
    `SplitModel, `DiagnosticFirstOwner, `TypedConsumer, `ExactTypes,
    env.mainModule
  ]
  for mod in origins do
    unless mod == env.mainModule || (env.getModuleIdx? mod).isSome do
      throwError "missing required imported module {mod}"
    logInfo m!"MAT009_MODULE {mod}"
  for mod in env.header.moduleNames do
    logInfo m!"MAT009_IMPORT {mod}"
  let allowed := #[`propext, `Quot.sound, `Classical.choice]
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
      let generated := name.toString.endsWith "_cstage1" ||
        name.toString.endsWith "_cstage2" ||
        (name.toString.splitOn "._closed_").length > 1 ||
        (name.toString.splitOn "._elambda_").length > 1
      if info matches .axiomInfo _ then
        unless generated do
          throwError "project axiom declaration {name}"
      let axioms ← collectAxioms name
      let unsafeDef : Bool := match info with
        | .defnInfo d => d.safety == DefinitionSafety.unsafe
        | _ => false
      for ax in axioms do
        unless allowed.contains ax || generated do
          throwError "unapproved transitive axiom {ax} in {name} (origin {origin})"
      if unsafeDef && !generated then
        throwError "unsafe project definition {name}"
      let row := Json.mkObj [
        ("origin", toJson origin.toString),
        ("declaration", toJson name.toString),
        ("kind", toJson (if generated then "compiler_auxiliary" else
          if info matches .thmInfo _ then "theorem" else "non_theorem")),
        ("is_axiom", toJson (info matches .axiomInfo _)),
        ("unsafe_definition", toJson unsafeDef),
        ("type", toJson (← liftTermElabM do
          pure (← Lean.Meta.ppExpr info.type).pretty)),
        ("axioms", toJson (axioms.map Name.toString))]
      logInfo m!"MAT009_DECL {row.compress}"
  if seen == 0 || theorems == 0 then
    throwError "empty proof inventory"
  logInfo m!"MAT009_AUDIT declarations={seen} theorems={theorems}"
