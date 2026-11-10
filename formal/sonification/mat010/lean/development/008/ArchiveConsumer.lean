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
    ∀ pair ∈ claims.zip snapshots, ValidPair pair.1 pair.2 :=
  M010_A3_pair_coverage h

example {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out) :
    ∀ artifact ∈ out,
      validName artifact.name = true ∧
      validDigest artifact.sha256 = true ∧
      (artifact.name.endsWith ".mid" = true → artifact.stage = firstStage) :=
  M010_A4_artifact_identities h

example {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out) :
    ∀ pair ∈ claims.zip snapshots,
      (sortMembers pair.2.members).Pairwise
        (fun left right => left.name ≤ right.name) :=
  M010_A5_per_stage_sorted h

example {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out) :
    (out.map Artifact.logicalPath).Nodup ∧
      out.getLast?.map Artifact.stage = some lastStage :=
  M010_A6_unique_paths_and_final_stage h

example {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out) :
    ∀ artifact ∈ out,
      artifact.logicalPath = logicalPath artifact.stage artifact.name ∧
      artifact.contentInThisManifest = hashOnly ∧
      artifact.audioRendered = false ∧
      ∃ snapshot ∈ snapshots, ∃ member ∈ snapshot.members,
        artifact = artifactOf snapshot member :=
  M010_A7_provenance_and_labels h

#print axioms M010_A1_ordered_nine
#print axioms M010_A2_commit_identities
#print axioms M010_A3_pair_coverage
#print axioms M010_A4_artifact_identities
#print axioms M010_A5_per_stage_sorted
#print axioms M010_A6_unique_paths_and_final_stage
#print axioms M010_A7_provenance_and_labels

end MAT010.Archive.Consumer
