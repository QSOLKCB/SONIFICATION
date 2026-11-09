import Std

/- Source-independent model. No claim about Python parsing, mutable dictionaries,
sets, exceptions, or implementation refinement is made by this module. -/
namespace Sonification.Mat008

structure ParsedRow where
  campaign : String
  originalRun : String

structure State where
  owner : List (String × String)
  conflict : Bool

def lookup : List (String × String) → String → Option String
  | [], _ => none
  | (run, campaign) :: rest, key => if key = run then some campaign else lookup rest key

def initial : State := ⟨[], false⟩

def differentOwner (s : State) (row : ParsedRow) : Bool :=
  match lookup s.owner row.originalRun with
  | none => false
  | some campaign => decide (campaign ≠ row.campaign)

def step (s : State) (row : ParsedRow) : State :=
  ⟨(row.originalRun, row.campaign) :: s.owner,
   differentOwner s row⟩

def scanFrom (s : State) : List ParsedRow → State
  | [] => s
  | row :: rows => scanFrom (step s row) rows

def scan (rows : List ParsedRow) : State := scanFrom initial rows

def Covers (s : State) (rows : List ParsedRow) : Prop :=
  ∀ row ∈ rows, lookup s.owner row.originalRun = some row.campaign


 theorem sticky_defect_counterexample :
     (scan [⟨"A", "RUN"⟩, ⟨"B", "RUN"⟩, ⟨"B", "OTHER"⟩]).conflict = false := by
   decide
 end Sonification.Mat008
