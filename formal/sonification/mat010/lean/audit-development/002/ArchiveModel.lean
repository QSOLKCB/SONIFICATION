import Std

/-!
An independent, executable model of the accepted archive-membership path in
the frozen MAT-SPEC-010 source. Inputs are arbitrary finite lists. A snapshot's
member list represents an exact built-in Python dictionary, so duplicate names
are rejected. The model has no Python exceptions, bytes, Git objects, SHA-256
implementation, filesystem, or physical-evidence interpretation.

`Artifact.name` is a model-only witness for the source member key. The Python
result contains `logical_path`, but omits this separate key.
-/

namespace MAT010.Archive

def stages : List String := [
  "MAT-SPEC-001", "MAT-SPEC-002", "MAT-SPEC-003",
  "MAT-SPEC-004", "MAT-SPEC-005", "MAT-SPEC-006",
  "MAT-SPEC-007", "MAT-SPEC-008", "MAT-SPEC-009"
]

def firstStage : String := "MAT-SPEC-001"
def lastStage : String := "MAT-SPEC-009"
def hashOnly : String := "HASH_ONLY_REBUILD_REQUIRED"

structure Claim where
  profile : String
  version : String
  mergedCommit : String
  evidenceFile : String
  deriving Repr

structure Member where
  name : String
  digest : String
  deriving Repr, DecidableEq

structure Snapshot where
  identifier : String
  version : String
  members : List Member
  deriving Repr

structure Artifact where
  stage : String
  version : String
  name : String
  logicalPath : String
  sha256 : String
  contentInThisManifest : String
  audioRendered : Bool
  deriving Repr

def lowerHex (c : Char) : Bool := "0123456789abcdef".toList.contains c

def validCommit (value : String) : Bool :=
  value.length == 40 && value.toList.all lowerHex

def validDigest (value : String) : Bool :=
  value.length == 64 && value.toList.all lowerHex

-- For a basename with no separator, this models the three permitted
-- `Path(name).suffix` outcomes. Leading dot-only stems have no suffix.
def allowedSuffix (name : String) : Bool :=
  match (name.splitOn ".").reverse with
  | extension :: preceding =>
      (extension == "json" || extension == "csv" || extension == "mid") &&
        preceding.any (· != "")
  | [] => false

def validName (name : String) : Bool :=
  name != "" && name != "." && name != ".." &&
    !(name.contains '/') && !(name.contains '\\') && allowedSuffix name

def ValidMember (stage : String) (member : Member) : Prop :=
  validName member.name = true ∧
    validDigest member.digest = true ∧
    (member.name.endsWith ".mid" = true → stage = firstStage)

instance (stage : String) (member : Member) : Decidable (ValidMember stage member) := by
  unfold ValidMember
  infer_instance

def ValidPair (claim : Claim) (snapshot : Snapshot) : Prop :=
  claim.version = snapshot.version ∧
    snapshot.members ≠ [] ∧
    claim.evidenceFile ∈ snapshot.members.map Member.name ∧
    (snapshot.members.map Member.name).Nodup ∧
    snapshot.members.all (fun member =>
      decide (ValidMember snapshot.identifier member)) = true

instance (claim : Claim) (snapshot : Snapshot) : Decidable (ValidPair claim snapshot) := by
  unfold ValidPair
  infer_instance

def stageSuffix (stage : String) : String :=
  stage.takeRight 3

def logicalPath (stage name : String) : String :=
  "dist/mat-spec-" ++ stageSuffix stage ++ "/" ++ name

def artifactOf (snapshot : Snapshot) (member : Member) : Artifact where
  stage := snapshot.identifier
  version := snapshot.version
  name := member.name
  logicalPath := logicalPath snapshot.identifier member.name
  sha256 := member.digest
  contentInThisManifest := hashOnly
  audioRendered := false

def memberLE (left right : Member) : Bool :=
  decide (left.name ≤ right.name)

def sortMembers (members : List Member) : List Member :=
  members.mergeSort memberLE

def emitFor (snapshot : Snapshot) : List Artifact :=
  (sortMembers snapshot.members).map (artifactOf snapshot)

def emit (claims : List Claim) (snapshots : List Snapshot) : List Artifact :=
  (claims.zip snapshots).flatMap (fun pair => emitFor pair.2)

def ValidInput (claims : List Claim) (snapshots : List Snapshot) : Prop :=
  claims.map Claim.profile = stages ∧
    snapshots.map Snapshot.identifier = stages ∧
    (claims.map Claim.mergedCommit).Nodup ∧
    claims.all (fun claim => validCommit claim.mergedCommit) = true ∧
    (claims.zip snapshots).all (fun pair =>
      decide (ValidPair pair.1 pair.2)) = true ∧
    ((emit claims snapshots).map Artifact.logicalPath).Nodup ∧
    (emit claims snapshots).getLast?.map Artifact.stage = some lastStage

instance (claims : List Claim) (snapshots : List Snapshot) :
    Decidable (ValidInput claims snapshots) := by
  unfold ValidInput
  infer_instance

def validate (claims : List Claim) (snapshots : List Snapshot) : Option (List Artifact) :=
  if ValidInput claims snapshots then some (emit claims snapshots) else none

private theorem success_conditions {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out) :
    ValidInput claims snapshots ∧ out = emit claims snapshots := by
  by_cases hv : ValidInput claims snapshots
  · simp [validate, hv] at h
    exact ⟨hv, h.symm⟩
  · simp [validate, hv] at h

theorem M010_A1_ordered_nine {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out) :
    claims.map Claim.profile = stages ∧
      snapshots.map Snapshot.identifier = stages ∧
      claims.length = 9 ∧ snapshots.length = 9 := by
  obtain ⟨⟨hc, hs, _, _, _, _, _⟩, _⟩ := success_conditions h
  have hcl : claims.length = 9 := by
    have heq := congrArg List.length hc
    simpa [stages] using heq
  have hsl : snapshots.length = 9 := by
    have heq := congrArg List.length hs
    simpa [stages] using heq
  exact ⟨hc, hs, hcl, hsl⟩

theorem M010_A2_commit_identities {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (h : validate claims snapshots = some out) :
    (claims.map Claim.mergedCommit).Nodup ∧
      ∀ claim ∈ claims, validCommit claim.mergedCommit = true := by
  obtain ⟨⟨_, _, hunique, hcommits, _, _, _⟩, _⟩ := success_conditions h
  exact ⟨hunique, fun claim hmem => (List.all_eq_true.mp hcommits) claim hmem⟩

theorem M010_A3_pair_coverage {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (h : validate claims snapshots = some out) :
    ∀ pair ∈ claims.zip snapshots, ValidPair pair.1 pair.2 := by
  obtain ⟨⟨_, _, _, _, hpairs, _, _⟩, _⟩ := success_conditions h
  intro pair hmem
  exact (decide_eq_true_eq).mp ((List.all_eq_true.mp hpairs) pair hmem)

private theorem emitted_source {claims : List Claim} {snapshots : List Snapshot}
    {out : List Artifact} (h : validate claims snapshots = some out)
    {artifact : Artifact} (ha : artifact ∈ out) :
    ∃ snapshot ∈ snapshots, ∃ member ∈ snapshot.members,
      artifact = artifactOf snapshot member ∧
        ValidMember snapshot.identifier member := by
  obtain ⟨_, hout⟩ := success_conditions h
  rw [hout, emit] at ha
  obtain ⟨pair, hpairmem, hfor⟩ := List.mem_flatMap.mp ha
  rcases pair with ⟨claim, snapshot⟩
  have hvalid := M010_A3_pair_coverage h (claim, snapshot) hpairmem
  have hsnapshot : snapshot ∈ snapshots := (List.of_mem_zip hpairmem).2
  unfold emitFor at hfor
  obtain ⟨member, hsorted, heq⟩ := List.mem_map.mp hfor
  have hmember : member ∈ snapshot.members :=
    (List.mem_mergeSort).mp hsorted
  have hwell : ValidMember snapshot.identifier member := by
    have hall := hvalid.2.2.2.2
    exact (decide_eq_true_eq).mp ((List.all_eq_true.mp hall) member hmember)
  exact ⟨snapshot, hsnapshot, member, hmember, heq.symm, hwell⟩

theorem M010_A4_artifact_identities {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (h : validate claims snapshots = some out) :
    ∀ artifact ∈ out,
      validName artifact.name = true ∧
      validDigest artifact.sha256 = true ∧
      (artifact.name.endsWith ".mid" = true → artifact.stage = firstStage) := by
  intro artifact ha
  obtain ⟨snapshot, _, member, _, heq, hwell⟩ := emitted_source h ha
  rw [heq]
  exact hwell

private theorem sortMembers_sorted (members : List Member) :
    (sortMembers members).Pairwise (fun left right => left.name ≤ right.name) := by
  have htrans : ∀ (a b c : Member), memberLE a b → memberLE b c →
      memberLE a c := by
    intro a b c hab hbc
    simp only [memberLE, decide_eq_true_eq] at hab hbc ⊢
    exact String.le_trans hab hbc
  have htotal : ∀ (a b : Member), memberLE a b || memberLE b a := by
    intro a b
    rcases String.le_total a.name b.name with hab | hba
    · simp [memberLE, hab]
    · simp [memberLE, hba]
  have hsorted := List.sorted_mergeSort htrans htotal members
  simpa [sortMembers, memberLE] using hsorted

theorem M010_A5_per_stage_sorted {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (_h : validate claims snapshots = some out) :
    ∀ pair ∈ claims.zip snapshots,
      (sortMembers pair.2.members).Pairwise
        (fun left right => left.name ≤ right.name) := by
  intro pair _
  exact sortMembers_sorted pair.2.members

theorem M010_A6_unique_paths_and_final_stage {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (h : validate claims snapshots = some out) :
    (out.map Artifact.logicalPath).Nodup ∧
      out.getLast?.map Artifact.stage = some lastStage := by
  obtain ⟨⟨_, _, _, _, _, hpaths, hlast⟩, hout⟩ := success_conditions h
  rw [hout]
  exact ⟨hpaths, hlast⟩

theorem M010_A7_provenance_and_labels {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (h : validate claims snapshots = some out) :
    ∀ artifact ∈ out,
      artifact.logicalPath = logicalPath artifact.stage artifact.name ∧
      artifact.contentInThisManifest = hashOnly ∧
      artifact.audioRendered = false ∧
      ∃ snapshot ∈ snapshots, ∃ member ∈ snapshot.members,
        artifact = artifactOf snapshot member := by
  intro artifact ha
  obtain ⟨snapshot, hsnapshot, member, hmember, heq, _⟩ := emitted_source h ha
  rw [heq]
  exact ⟨rfl, rfl, rfl, snapshot, hsnapshot, member, hmember, rfl⟩

end MAT010.Archive
