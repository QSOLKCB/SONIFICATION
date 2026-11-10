import SplitModel
import DiagnosticFirstOwner

/-!
A separate import consumer for the MAT009 split model. These declarations
type-check the public R1–R7 interface and derive blocked outcomes from the
generic finite-scan and parent-reason theorems.
-/

namespace MAT009.Consumer

#check M009_R1_initial
#check M009_R2_assignment_overwrite
#check M009_R3_cross_role_trigger
#check M009_R4_stickiness
#check M009_R5_final_set_intersection
#check M009_R5_parent_union
#check M009_R6_cross_trigger_in_finite_scan
#check M009_R6_arbitrary_finite_scan
#check M009_R6_latest_owner
#check M009_R6_parent_reason_survives
#check M009_R6_final_leakage_iff
#check M009_R7_accepted_example
#check M009_R7_rejected_example
#check M009_R7_nonvacuous
#check MAT009.Diagnostic.scan_first_owner_sticky

theorem parent_reason_blocks_any_scan (parent : ReasonSet)
    (rows : List Row) (reason : String) (h : parent reason) :
    (finalize (scan (initial parent) rows)).status = .blocked := by
  apply (Final.status_blocked_iff _).2
  exact ⟨reason, M009_R6_parent_reason_survives parent rows reason h⟩

theorem shared_campaign_blocks_any_scan (parent : ReasonSet)
    (rows : List Row) (campaign : String)
    (htrain : ∃ row ∈ rows,
      row.role = .train ∧ row.campaign = campaign)
    (hholdout : ∃ row ∈ rows,
      row.role = .holdout ∧ row.campaign = campaign) :
    (finalize (scan (initial parent) rows)).status = .blocked := by
  apply (Final.status_blocked_iff _).2
  refine ⟨leakageReason, Or.inr ?_⟩
  exact (M009_R6_final_leakage_iff parent rows).2
    (Or.inl ⟨campaign, htrain, hholdout⟩)

#print axioms M009_R1_initial
#print axioms M009_R2_assignment_overwrite
#print axioms M009_R3_cross_role_trigger
#print axioms M009_R4_stickiness
#print axioms M009_R5_final_set_intersection
#print axioms M009_R5_parent_union
#print axioms M009_R6_cross_trigger_in_finite_scan
#print axioms M009_R6_arbitrary_finite_scan
#print axioms M009_R6_latest_owner
#print axioms M009_R6_parent_reason_survives
#print axioms M009_R6_final_leakage_iff
#print axioms M009_R7_accepted_example
#print axioms M009_R7_rejected_example
#print axioms M009_R7_nonvacuous
#print axioms parent_reason_blocks_any_scan
#print axioms shared_campaign_blocks_any_scan
#print axioms MAT009.Diagnostic.scan_first_owner_sticky
#print axioms MAT009.Diagnostic.first_owner_not_last_writer

end MAT009.Consumer
