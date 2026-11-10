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
  /- Lean 4.19.0 emits these exact unsafe specialization axioms for the
     pinned ArchiveModel source. They are compiler mechanisms, not premises
     allowed in any ordinary model theorem or definition. The Python verifier
     pins each type and the complete generated declaration inventory. -/
  let trustedProjectCompilerAxioms := #[
    "List.flatMapTR.go._at.MAT010.Archive.emit._spec_1",
    "List.foldl._at.MAT010.Archive.stageSuffix._spec_1",
    "List.hasDecEq._at.MAT010.Archive.instDecidableValidInput._spec_2",
    "List.hasDecEq._at.MAT010.Archive.instDecidableValidPair._spec_1",
    "List.isPrefixOf._at._private.ArchiveModel.0.MAT010.Archive.suffixCase._spec_1",
    "List.isSuffixOf._at.MAT010.Archive.hasMidiSuffix._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.demoClaims._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.demoSnapshots._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.demoSnapshotsExtra._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.emitFor._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.instDecidableValidInput._spec_1",
    "List.mapTR.loop._at.MAT010.Archive.instDecidableValidInput._spec_3",
    "List.mapTR.loop._at.MAT010.Archive.instDecidableValidInput._spec_4",
    "List.mapTR.loop._at.MAT010.Archive.instDecidableValidInput._spec_5",
    "List.mapTR.loop._at.MAT010.Archive.instDecidableValidPair._spec_2"
  ]
  /- These are imported compiler mechanisms in the pinned Lean toolchain.
     `lcProof` is unsafe compiler bookkeeping. Their import bytes are recorded
     in the accepted receipt. Ordinary logical declarations cannot use them. -/
  let trustedImportedCompilerAxioms := #[
    "List.elem._at.System.FilePath.normalize._spec_1",
    "_private.Init.Data.Option.Basic.0.Option.decEqOption.«_@».Init.Data.Option.Basic._hyg.4._at.Std.Time.Database.TZdb.idFromPath._spec_1",
    "lcProof"
  ]
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
      let compilerAux := (unsafeDef || unsafeAxiom) && !hasSourceRange
      if info matches .axiomInfo _ then
        unless compilerAux && trustedProjectCompilerAxioms.contains name.toString do
          throwError "project axiom declaration {name}"
      if unsafeDef && !compilerAux then
        throwError "unsafe project definition {name}"
      let axioms ← collectAxioms name
      for ax in axioms do
        unless allowedLogical.contains ax ||
            (compilerAux &&
              (trustedProjectCompilerAxioms.contains ax.toString ||
               trustedImportedCompilerAxioms.contains ax.toString)) do
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
      logInfo m!"MAT010_DECL {row.compress}"
  if seen == 0 || theorems < 7 then
    throwError "incomplete proof inventory"
  logInfo m!"MAT010_AUDIT declarations={seen} theorems={theorems}"
