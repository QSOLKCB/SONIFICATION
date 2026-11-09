import Std

/- An abstract strict total order contract. Its laws are hypotheses, not axioms.
No instantiation to CPython Fraction is supplied or claimed. -/
namespace Sonification.Ordered

structure OrderSpec (α : Type) where
  lt : α → α → Prop
  decLt : DecidableRel lt
  irrefl : ∀ x, ¬lt x x
  trans : ∀ {x y z}, lt x y → lt y z → lt x z
  lt_of_lt_of_not_gt : ∀ {x y z}, lt x y → ¬lt z y → lt x z

attribute [instance] OrderSpec.decLt

structure Interval (α : Type) where
  lo : α
  hi : α

inductive Relation where
  | below | above | overlap
  deriving DecidableEq

def Valid (o : OrderSpec α) (a : Interval α) : Prop := ¬o.lt a.hi a.lo

def classify (o : OrderSpec α) (a b : Interval α) : Option Relation :=
  if o.lt a.hi a.lo ∨ o.lt b.hi b.lo then none
  else if o.lt a.hi b.lo then some .below
  else if o.lt b.hi a.lo then some .above
  else some .overlap

def map (f : α → β) (a : Interval α) : Interval β := ⟨f a.lo, f a.hi⟩

theorem separation_exclusive (o : OrderSpec α) (a b : Interval α)
    (ha : Valid o a) (hb : Valid o b) :
    ¬(o.lt a.hi b.lo ∧ o.lt b.hi a.lo) := by
  intro h
  have x : o.lt a.hi b.hi := o.lt_of_lt_of_not_gt h.1 hb
  have y : o.lt b.hi a.hi := o.lt_of_lt_of_not_gt h.2 ha
  exact o.irrefl _ (o.trans x y)

/- A direct small order consequence is isolated so every premise stays visible. -/
theorem asymmetric (o : OrderSpec α) {x y : α} (h : o.lt x y) : ¬o.lt y x := by
  intro hr
  exact o.irrefl x (o.trans h hr)

theorem classify_below_iff (o : OrderSpec α) (a b : Interval α) :
    classify o a b = some .below ↔ Valid o a ∧ Valid o b ∧ o.lt a.hi b.lo := by
  by_cases h1 : o.lt a.hi a.lo ∨ o.lt b.hi b.lo <;>
    by_cases h2 : o.lt a.hi b.lo <;> by_cases h3 : o.lt b.hi a.lo <;>
    simp_all [classify, Valid] <;> intro h <;> exact h1.resolve_left h

theorem classify_overlap_iff (o : OrderSpec α) (a b : Interval α) :
    classify o a b = some .overlap ↔
      Valid o a ∧ Valid o b ∧ ¬o.lt a.hi b.lo ∧ ¬o.lt b.hi a.lo := by
  by_cases h1 : o.lt a.hi a.lo ∨ o.lt b.hi b.lo <;>
    by_cases h2 : o.lt a.hi b.lo <;> by_cases h3 : o.lt b.hi a.lo <;>
    simp_all [classify, Valid] <;> intro h <;> exact h1.resolve_left h

theorem exhaustive (o : OrderSpec α) (a b : Interval α)
    (ha : Valid o a) (hb : Valid o b) :
    classify o a b = some .below ∨ classify o a b = some .above ∨
      classify o a b = some .overlap := by
  have h1 : ¬(o.lt a.hi a.lo ∨ o.lt b.hi b.lo) := fun h => h.elim ha hb
  by_cases h2 : o.lt a.hi b.lo <;> by_cases h3 : o.lt b.hi a.lo <;>
    simp [classify, h1, h2, h3]

theorem order_reflecting_map (o : OrderSpec α) (p : OrderSpec β)
    (f : α → β) (h : ∀ x y, p.lt (f x) (f y) ↔ o.lt x y)
    (a b : Interval α) :
    classify p (map f a) (map f b) = classify o a b := by
  simp only [classify, map, h]

end Sonification.Ordered
