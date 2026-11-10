import ArchiveModel

/-!
Typed import consumer for the seven Phase A archive-model theorems. Each
`example` fixes the complete public theorem type expected by this phase.
-/

namespace MAT010.Archive.Consumer

open MAT010.Archive

example {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out) :
    claims.map Claim.profile = stages ∧
      snapshots.map Snapshot.identifier = stages ∧
      claims.length = 9 ∧ snapshots.length = 9 :=
  M010_A1_ordered_nine h

example {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out) :
    (claims.map Claim.mergedCommit).Nodup ∧
      ∀ claim ∈ claims, validCommit claim.mergedCommit = true :=
  M010_A2_commit_identities h

example {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out) :
    ∀ artifact ∈ out,
      artifact.stage ∈ stages ∧
      validName artifact.name = true ∧
      validDigest artifact.sha256 = true ∧
      (hasMidiSuffix artifact.name = true → artifact.stage = firstStage) ∧
      ∃ claim snapshot member,
        (claim, snapshot) ∈ claims.zip snapshots ∧
        member ∈ snapshot.members ∧
        claim.version = artifact.version ∧
        artifact = artifactOf snapshot member :=
  M010_A3_valid_artifact_identity h

example {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out) :
    (out.map Artifact.logicalPath).Nodup ∧
      out.getLast?.map Artifact.stage = some lastStage :=
  M010_A4_unique_logical_paths h

example (claims : List Claim) {left right : List Snapshot}
    (hequiv : SameMaps left right)
    (hkeys : ∀ snapshot ∈ left,
      (snapshot.members.map Member.name).Nodup) :
    emit claims left = emit claims right ∧
      validate claims left = validate claims right :=
  M010_A5_deterministic_enumeration claims hequiv hkeys

example (claims : List Claim) (snapshots : List Snapshot)
    (h : Malformed claims snapshots) :
    validate claims snapshots = none :=
  M010_A6_fail_closed_malformed claims snapshots h

example :
    (validate demoClaims demoSnapshots).isSome = true ∧
    (validate demoClaims demoSnapshotsExtra).isSome = true ∧
    (validate demoClaims []).isNone = true :=
  M010_A7_accepted_and_rejected_nonvacuity

#print axioms M010_A1_ordered_nine
#print axioms M010_A2_commit_identities
#print axioms M010_A3_valid_artifact_identity
#print axioms M010_A4_unique_logical_paths
#print axioms M010_A5_deterministic_enumeration
#print axioms M010_A6_fail_closed_malformed
#print axioms M010_A7_accepted_and_rejected_nonvacuity

end MAT010.Archive.Consumer
