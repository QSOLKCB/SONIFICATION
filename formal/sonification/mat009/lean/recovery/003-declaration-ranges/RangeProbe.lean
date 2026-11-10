import ExactTypes
import Lean
open Lean Elab Command
run_cmd do
  for n in [`MAT009.initial._elambda_1, `MAT009.step._elambda_1,
            `MAT009.auditor_false_cstage1, `MAT009.auditor_false_proof_cstage1,
            `MAT009.initial._cstage1, `MAT009.initial] do
    let r ← findDeclarationRangesCore? n
    logInfo m!"RANGE {n} {r.isSome}"
