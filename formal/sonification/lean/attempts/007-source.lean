import Std

/- An abstract strict total order contract. Its laws are hypotheses, not axioms.
No instantiation to CPython Fraction is supplied or claimed. -/
namespace Sonification.Ordered

structure OrderSpec (α : Type) where
  lt : α → α → Prop
  decLt : DecidableRel lt
  irrefl : ∀ x, ¬lt x x
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
  have z : o.lt a.hi a.hi := o.lt_of_lt_of_not_gt x (fun h' => o.irrefl _ (o.lt_of_lt_of_not_gt h' (fun h'' => o.irrefl _ (o.lt_of_lt_of_not_gt y (fun _ => h'')))))
  exact o.irrefl _ z

/- A direct small order consequence is isolated so every premise stays visible. -/
theorem asymmetric (o : OrderSpec α) {x y : α} (h : o.lt x y) : ¬o.lt y x := by
  intro hr
  exact o.irrefl x (o.lt_of_lt_of_not_gt h (fun he => o.irrefl y he))

end Sonification.Ordered
