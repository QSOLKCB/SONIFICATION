import Std

/-!
The MAT009 diagnostic hash and event registries use the same `setdefault`
ownership rule. This abstract registry models one such identity map. It is
separate from the campaign split model and assumes identities were already
validated before registration.
-/

namespace MAT009.Diagnostic

abbrev Owner := String × String -- campaign and role
abbrev Registry := String → Option Owner

def empty : Registry := fun _ => none

def register (registry : Registry) (identity : String)
    (candidate : Owner) : Registry :=
  fun key =>
    if key = identity then
      match registry key with
      | none => some candidate
      | some first => some first
    else
      registry key

def scan (registry : Registry) : List (String × Owner) → Registry
  | [] => registry
  | (identity, candidate) :: rest =>
      scan (register registry identity candidate) rest

theorem register_first_owner (registry : Registry)
    (identity : String) (candidate first : Owner)
    (h : registry identity = some first) :
    (register registry identity candidate) identity = some first := by
  simp [register, h]

theorem register_new_owner (registry : Registry)
    (identity : String) (candidate : Owner)
    (h : registry identity = none) :
    (register registry identity candidate) identity = some candidate := by
  simp [register, h]

theorem register_other_identity (registry : Registry)
    (identity key : String) (candidate : Owner)
    (h : key ≠ identity) :
    (register registry identity candidate) key = registry key := by
  simp [register, h]

theorem register_preserves_existing (registry : Registry)
    (identity key : String) (candidate first : Owner)
    (h : registry key = some first) :
    (register registry identity candidate) key = some first := by
  by_cases hkey : key = identity
  · subst key
    simp [register, h]
  · simp [register, hkey, h]

theorem scan_first_owner_sticky (registry : Registry)
    (updates : List (String × Owner)) (key : String) (first : Owner)
    (h : registry key = some first) :
    (scan registry updates) key = some first := by
  induction updates generalizing registry with
  | nil => simpa [scan] using h
  | cons update rest ih =>
      rcases update with ⟨identity, candidate⟩
      exact ih (registry := register registry identity candidate)
        (register_preserves_existing registry identity key candidate first h)

-- A second claimant cannot change the first owner of a diagnostic identity.
theorem first_owner_not_last_writer :
    (scan empty
      [("D", ("CAMPAIGN_A", "TRAIN")),
       ("D", ("CAMPAIGN_B", "HOLDOUT"))]) "D" =
      some ("CAMPAIGN_A", "TRAIN") := by
  simp [scan, register, empty]

end MAT009.Diagnostic
