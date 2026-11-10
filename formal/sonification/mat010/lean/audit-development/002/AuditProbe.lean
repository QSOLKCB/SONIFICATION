import ArchiveConsumer
import Lean
open Lean Elab Command
run_cmd do
  let env ← getEnv
  let origins := #[`ArchiveModel, `ArchiveConsumer, env.mainModule]
  let mut seen : Nat := 0
  let mut theorems : Nat := 0
  for (name, info) in env.checked.get.constants.toList do
    let origin := match env.getModuleIdxFor? name with
      | some idx => env.header.moduleNames[idx.toNat]!
      | none => env.mainModule
    if origins.contains origin then
      seen := seen + 1
      if info matches .thmInfo _ then theorems := theorems + 1
      let unsafeDef : Bool := match info with
        | .defnInfo d => d.safety == DefinitionSafety.unsafe
        | _ => false
      let unsafeAxiom : Bool := match info with
        | .axiomInfo a => a.isUnsafe
        | _ => false
      if (info matches .axiomInfo _) || unsafeDef then
        let hasSourceRange := (← findDeclarationRangesCore? name).isSome
        let typeStr ← liftTermElabM do
          pure (← Lean.Meta.ppExpr info.type).pretty
        let axioms ← collectAxioms name
        let row := Json.mkObj [
          ("origin",toJson origin.toString),
          ("declaration",toJson name.toString),
          ("is_axiom",toJson (info matches .axiomInfo _)),
          ("unsafe_axiom",toJson unsafeAxiom),
          ("unsafe_definition",toJson unsafeDef),
          ("has_source_range",toJson hasSourceRange),
          ("type",toJson typeStr),
          ("axioms",toJson (axioms.map Name.toString))]
        logInfo m!"PROBE_DECL {row.compress}"
  logInfo m!"PROBE_SUMMARY declarations={seen} theorems={theorems}"
