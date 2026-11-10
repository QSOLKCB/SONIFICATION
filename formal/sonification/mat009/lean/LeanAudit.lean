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
  let allowedLogical := #[`propext, `Quot.sound, `Classical.choice]
  /- These unsafe axioms are emitted by Lean's compiler for the two recursive
     model functions. `lcProof` and `lcUnreachable` are compiler mechanisms used
     only by unsafe generated definitions, never by logical theorems. -/
  let allowedCompiler := #[`lcProof, `lcUnreachable,
    `MAT009.initial._elambda_1, `MAT009.step._elambda_1]
  let mut seen : Nat := 0
  let mut theorems : Nat := 0
  let mut compilerAxioms : Nat := 0
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
      let generatedName := name.toString.endsWith "_cstage1" ||
        name.toString.endsWith "_cstage2" ||
        (name.toString.splitOn "._closed_").length > 1 ||
        (name.toString.splitOn "._elambda_").length > 1
      let unsafeDef : Bool := match info with
        | .defnInfo d => d.safety == DefinitionSafety.unsafe
        | _ => false
      let unsafeAxiom : Bool := match info with
        | .axiomInfo a => a.isUnsafe
        | _ => false
      let hasSourceRange := (← findDeclarationRangesCore? name).isSome
      let compilerAux := (unsafeDef || unsafeAxiom) && !hasSourceRange
      let typeStr ← liftTermElabM do
        pure (← Lean.Meta.ppExpr info.type).pretty
      if info matches .axiomInfo _ then
        let expectedType : Option String :=
          if name == `MAT009.initial._elambda_1 then
            some "String → Option MAT009.Role"
          else if name == `MAT009.step._elambda_1 then
            some "MAT009.State → MAT009.Row → String → Option MAT009.Role"
          else
            none
        unless compilerAux && expectedType == some typeStr do
          throwError "project axiom declaration {name}"
        compilerAxioms := compilerAxioms + 1
      if unsafeDef && !(compilerAux && generatedName) then
        throwError "unsafe project definition {name}"
      let axioms ← collectAxioms name
      for ax in axioms do
        unless allowedLogical.contains ax ||
            (compilerAux && allowedCompiler.contains ax) do
          throwError "unapproved transitive axiom {ax} in {name} (origin {origin})"
      let row := Json.mkObj [
        ("origin", toJson origin.toString),
        ("declaration", toJson name.toString),
        ("kind", toJson (if compilerAux then "compiler_auxiliary" else
          if info matches .thmInfo _ then "theorem" else "non_theorem")),
        ("is_axiom", toJson (info matches .axiomInfo _)),
        ("unsafe_axiom", toJson unsafeAxiom),
        ("unsafe_definition", toJson unsafeDef),
        ("has_source_range", toJson hasSourceRange),
        ("type", toJson typeStr),
        ("axioms", toJson (axioms.map Name.toString))]
      logInfo m!"MAT009_DECL {row.compress}"
  if seen == 0 || theorems == 0 || compilerAxioms != 2 then
    throwError "incomplete proof inventory"
  logInfo m!"MAT009_AUDIT declarations={seen} theorems={theorems}"
