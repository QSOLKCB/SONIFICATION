import ExactTypes
import Lean
open Lean Elab Command
run_cmd do
  let env ← getEnv
  for n in [`MAT009.initial._elambda_1, `MAT009.step._elambda_1,
            `MAT009.auditor_false_cstage1, `lcProof, `lcUnreachable] do
    match env.find? n with
    | some (.axiomInfo a) => logInfo m!"AXIOM {n} unsafe={a.isUnsafe} type={a.type}"
    | some _ => logInfo m!"NOT_AXIOM {n}"
    | none => logInfo m!"MISSING {n}"
