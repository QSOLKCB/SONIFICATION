import Sonification
import Lean

namespace SonificationStatementChecks
open Sonification
namespace IntegerChecks

def Sonification_invalid_iff (a b : Interval) :
    classify a b = none ↔ ¬Valid a ∨ ¬Valid b := Sonification.invalid_iff

def Sonification_below_iff (a b : Interval) :
    classify a b = some .below ↔ Valid a ∧ Valid b ∧ a.hi < b.lo := Sonification.below_iff

def Sonification_above_iff (a b : Interval) :
    classify a b = some .above ↔ Valid a ∧ Valid b ∧ b.hi < a.lo := Sonification.above_iff

def Sonification_overlap_iff (a b : Interval) :
    classify a b = some .overlap ↔
      Valid a ∧ Valid b ∧ a.lo ≤ b.hi ∧ b.lo ≤ a.hi := Sonification.overlap_iff

def Sonification_exhaustive (a b : Interval) (ha : Valid a) (hb : Valid b) :
    classify a b = some .below ∨ classify a b = some .above ∨
      classify a b = some .overlap := Sonification.exhaustive

def Sonification_exclusive (a b : Interval) (ha : Valid a) (hb : Valid b) :
    ¬(a.hi < b.lo ∧ b.hi < a.lo) ∧
    ¬(a.hi < b.lo ∧ (a.lo ≤ b.hi ∧ b.lo ≤ a.hi)) ∧
    ¬(b.hi < a.lo ∧ (a.lo ≤ b.hi ∧ b.lo ≤ a.hi)) := Sonification.exclusive

def Sonification_reversal (a b : Interval) :
    classify b a = (classify a b).map reverse := Sonification.reversal

def Sonification_scale_lt_iff (k x y : Int) (hk : 0 < k) :
    k * x < k * y ↔ x < y := Sonification.scale_lt_iff

def Sonification_positive_scale (k : Int) (a b : Interval) (hk : 0 < k) :
    classify (scale k a) (scale k b) = classify a b := Sonification.positive_scale

def Sonification_box_valid (center error : Int) (he : 0 ≤ error) :
    Valid (box center error) := Sonification.box_valid

def Sonification_touching (a b : Interval) (ha : Valid a) (hb : Valid b)
    (h : a.hi = b.lo) : classify a b = some .overlap := Sonification.touching

def Sonification_inhabited_branches :
    classify ⟨0, 1⟩ ⟨2, 3⟩ = some .below ∧
    classify ⟨2, 3⟩ ⟨0, 1⟩ = some .above ∧
    classify ⟨0, 1⟩ ⟨1, 2⟩ = some .overlap ∧
    classify ⟨1, 0⟩ ⟨0, 0⟩ = none := Sonification.inhabited_branches

end IntegerChecks
namespace OrderedChecks
open Sonification.Ordered

def Sonification_Ordered_separation_exclusive (o : OrderSpec α) (a b : Interval α)
    (ha : Valid o a) (hb : Valid o b) :
    ¬(o.lt a.hi b.lo ∧ o.lt b.hi a.lo) := Sonification.Ordered.separation_exclusive

def Sonification_Ordered_asymmetric (o : OrderSpec α) {x y : α} (h : o.lt x y) : ¬o.lt y x := Sonification.Ordered.asymmetric

def Sonification_Ordered_classify_below_iff (o : OrderSpec α) (a b : Interval α) :
    classify o a b = some .below ↔ Valid o a ∧ Valid o b ∧ o.lt a.hi b.lo := Sonification.Ordered.classify_below_iff

def Sonification_Ordered_classify_overlap_iff (o : OrderSpec α) (a b : Interval α) :
    classify o a b = some .overlap ↔
      Valid o a ∧ Valid o b ∧ ¬o.lt a.hi b.lo ∧ ¬o.lt b.hi a.lo := Sonification.Ordered.classify_overlap_iff

def Sonification_Ordered_exhaustive (o : OrderSpec α) (a b : Interval α)
    (ha : Valid o a) (hb : Valid o b) :
    classify o a b = some .below ∨ classify o a b = some .above ∨
      classify o a b = some .overlap := Sonification.Ordered.exhaustive

def Sonification_Ordered_order_reflecting_map (o : OrderSpec α) (p : OrderSpec β)
    (f : α → β) (h : ∀ x y, p.lt (f x) (f y) ↔ o.lt x y)
    (a b : Interval α) :
    classify p (map f a) (map f b) = classify o a b := Sonification.Ordered.order_reflecting_map

def Sonification_Ordered_integer_specialization (a b : Sonification.Interval) :
    classify integerOrder ⟨a.lo, a.hi⟩ ⟨b.lo, b.hi⟩ =
      (Sonification.classify a b).map (fun r => match r with
        | .below => .below | .above => .above | .overlap => .overlap) := Sonification.Ordered.integer_specialization

end OrderedChecks
end SonificationStatementChecks

namespace SonificationAudit
open Lean Elab Command

def audit : CommandElabM Unit := do
  let env ← getEnv
  let originModules := #[`Sonification.Intervals, `Sonification.OrderedIntervals, `Sonification, env.mainModule]
  let allowed := #[`propext, `Quot.sound, `Classical.choice]
  let mut seen : Nat := 0
  let mut theorems : Nat := 0
  for (name, info) in env.constants.toList do
    let origin := match env.getModuleIdxFor? name with
      | some idx => env.header.moduleNames[idx.toNat]!
      | none => env.mainModule
    if originModules.contains origin then
      seen := seen + 1
      if info matches .thmInfo _ then
        theorems := theorems + 1
      let axioms ← collectAxioms name
      for ax in axioms do
        unless allowed.contains ax do
          throwError "unapproved transitive axiom {ax} in {name} (origin {origin})"
      if info matches .axiomInfo _ then
        throwError "project axiom declaration {name}"
      let row := Json.mkObj [
        ("origin", toJson origin.toString),
        ("declaration", toJson name.toString),
        ("kind", toJson (if info matches .thmInfo _ then "theorem" else "non_theorem")),
        ("type", toJson (← ppExpr info.type).pretty),
        ("axioms", toJson (axioms.map Name.toString))]
      logInfo m!"SONIFICATION_DECL {row.compress}"
  if seen == 0 || theorems == 0 then
    throwError "empty proof inventory"
  logInfo m!"SONIFICATION_AUDIT declarations={seen} theorems={theorems}"

end SonificationAudit

run_cmd SonificationAudit.audit
