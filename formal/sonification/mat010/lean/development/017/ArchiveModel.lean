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

structure Member where
  name : String
  digest : String
  deriving DecidableEq

structure Snapshot where
  identifier : String
  version : String
  members : List Member

structure Artifact where
  stage : String
  version : String
  name : String
  logicalPath : String
  sha256 : String
  contentInThisManifest : String
  audioRendered : Bool

def lowerHex (c : Char) : Bool := "0123456789abcdef".toList.contains c

def validCommit (value : String) : Bool :=
  value.length == 40 && value.toList.all lowerHex

def validDigest (value : String) : Bool :=
  value.length == 64 && value.toList.all lowerHex

private def suffixCase (chars extension : List Char) : Bool :=
  let reversed := chars.reverse
  let marker := extension.reverse ++ ['.']
  marker.isPrefixOf reversed && (reversed.drop marker.length).any (· != '.')

-- For a basename with no separator, this models the three permitted
-- `Path(name).suffix` outcomes. Leading dot-only stems have no suffix.
def allowedSuffix (name : String) : Bool :=
  let chars := name.toList
  suffixCase chars "json".toList || suffixCase chars "csv".toList ||
    suffixCase chars "mid".toList

def validName (name : String) : Bool :=
  let chars := name.toList
  name != "" && name != "." && name != ".." &&
    !(chars.contains '/') && !(chars.contains '\\') && allowedSuffix name

def hasMidiSuffix (name : String) : Bool :=
  ".mid".toList.isSuffixOf name.toList

def ValidMember (stage : String) (member : Member) : Prop :=
  validName member.name = true ∧
    validDigest member.digest = true ∧
    (hasMidiSuffix member.name = true → stage = firstStage)

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
  ((stage.toList.reverse.take 3).reverse).foldl String.push ""

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

theorem pair_coverage {claims : List Claim}
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
  have hvalid := pair_coverage h (claim, snapshot) hpairmem
  have hsnapshot : snapshot ∈ snapshots := (List.of_mem_zip hpairmem).2
  unfold emitFor at hfor
  obtain ⟨member, hsorted, heq⟩ := List.mem_map.mp hfor
  have hmember : member ∈ snapshot.members :=
    (List.mem_mergeSort).mp hsorted
  have hwell : ValidMember snapshot.identifier member := by
    have hall := hvalid.2.2.2.2
    exact (decide_eq_true_eq).mp ((List.all_eq_true.mp hall) member hmember)
  exact ⟨snapshot, hsnapshot, member, hmember, heq.symm, hwell⟩

theorem artifact_identities {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (h : validate claims snapshots = some out) :
    ∀ artifact ∈ out,
      validName artifact.name = true ∧
      validDigest artifact.sha256 = true ∧
      (hasMidiSuffix artifact.name = true → artifact.stage = firstStage) := by
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

theorem per_stage_sorted {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (_h : validate claims snapshots = some out) :
    ∀ pair ∈ claims.zip snapshots,
      (sortMembers pair.2.members).Pairwise
        (fun left right => left.name ≤ right.name) := by
  intro pair _
  exact sortMembers_sorted pair.2.members

theorem M010_A4_unique_logical_paths {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (h : validate claims snapshots = some out) :
    (out.map Artifact.logicalPath).Nodup ∧
      out.getLast?.map Artifact.stage = some lastStage := by
  obtain ⟨⟨_, _, _, _, _, hpaths, hlast⟩, hout⟩ := success_conditions h
  rw [hout]
  exact ⟨hpaths, hlast⟩

theorem provenance_and_labels {claims : List Claim}
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

private theorem emitted_pair_source {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (h : validate claims snapshots = some out)
    {artifact : Artifact} (ha : artifact ∈ out) :
    ∃ claim snapshot member,
      (claim, snapshot) ∈ claims.zip snapshots ∧
      member ∈ snapshot.members ∧
      artifact = artifactOf snapshot member ∧
      ValidMember snapshot.identifier member := by
  obtain ⟨_, hout⟩ := success_conditions h
  rw [hout, emit] at ha
  obtain ⟨pair, hpairmem, hfor⟩ := List.mem_flatMap.mp ha
  rcases pair with ⟨claim, snapshot⟩
  have hvalid := pair_coverage h (claim, snapshot) hpairmem
  unfold emitFor at hfor
  obtain ⟨member, hsorted, heq⟩ := List.mem_map.mp hfor
  have hmember : member ∈ snapshot.members :=
    (List.mem_mergeSort).mp hsorted
  have hwell : ValidMember snapshot.identifier member := by
    have hall := hvalid.2.2.2.2
    exact (decide_eq_true_eq).mp ((List.all_eq_true.mp hall) member hmember)
  exact ⟨claim, snapshot, member, hpairmem, hmember, heq.symm, hwell⟩

theorem M010_A3_valid_artifact_identity {claims : List Claim}
    {snapshots : List Snapshot} {out : List Artifact}
    (h : validate claims snapshots = some out) :
    ∀ artifact ∈ out,
      artifact.stage ∈ stages ∧
      validName artifact.name = true ∧
      validDigest artifact.sha256 = true ∧
      (hasMidiSuffix artifact.name = true → artifact.stage = firstStage) ∧
      ∃ claim snapshot member,
        (claim, snapshot) ∈ claims.zip snapshots ∧
        member ∈ snapshot.members ∧
        claim.version = artifact.version ∧
        artifact = artifactOf snapshot member := by
  intro artifact ha
  obtain ⟨claim, snapshot, member, hpairmem, hmember, heq, hwell⟩ :=
    emitted_pair_source h ha
  have hids := (success_conditions h).1.2.1
  have hsnapshot : snapshot ∈ snapshots := (List.of_mem_zip hpairmem).2
  have hstage : snapshot.identifier ∈ stages := by
    rw [← hids]
    exact List.mem_map_of_mem hsnapshot
  have hversion : claim.version = snapshot.version :=
    (pair_coverage h (claim, snapshot) hpairmem).1
  rw [heq]
  exact ⟨hstage, hwell.1, hwell.2.1, hwell.2.2,
    claim, snapshot, member, hpairmem, hmember, hversion, rfl⟩

private theorem same_name_same_member (members : List Member)
    (hkeys : (members.map Member.name).Nodup)
    {left right : Member} (hl : left ∈ members) (hr : right ∈ members)
    (hname : left.name = right.name) : left = right := by
  induction members generalizing left right with
  | nil => simp at hl
  | cons head tail ih =>
      simp only [List.map_cons, List.nodup_cons] at hkeys
      obtain ⟨hhead, htail⟩ := hkeys
      simp only [List.mem_cons] at hl hr
      rcases hl with rfl | hl
      · rcases hr with rfl | hr
        · rfl
        · have hm : right.name ∈ tail.map Member.name :=
            List.mem_map_of_mem hr
          rw [← hname] at hm
          exact False.elim (hhead hm)
      · rcases hr with rfl | hr
        · have hm : left.name ∈ tail.map Member.name :=
            List.mem_map_of_mem hl
          rw [hname] at hm
          exact False.elim (hhead hm)
        · exact ih htail hl hr hname

private theorem sortMembers_perm_eq (left right : List Member)
    (hperm : left.Perm right)
    (hkeys : (left.map Member.name).Nodup) :
    sortMembers left = sortMembers right := by
  have hp : (sortMembers left).Perm (sortMembers right) :=
    (List.mergeSort_perm left memberLE).trans
      (hperm.trans (List.mergeSort_perm right memberLE).symm)
  apply List.Perm.eq_of_sorted
    (le := fun a b : Member => a.name ≤ b.name)
    (l₁ := sortMembers left) (l₂ := sortMembers right)
  · intro a b ha hb hab hba
    have hal : a ∈ left := by simpa [sortMembers] using ha
    have hbr : b ∈ right := by simpa [sortMembers] using hb
    have hbl : b ∈ left := hperm.symm.subset hbr
    exact same_name_same_member left hkeys hal hbl
      (String.le_antisymm hab hba)
  · exact sortMembers_sorted left
  · exact sortMembers_sorted right
  · exact hp

/-- Equal stage metadata and equal finite member maps, with insertion order
allowed to differ. Full `(name, digest)` pairs are permuted together. -/
inductive SameMaps : List Snapshot → List Snapshot → Prop where
  | nil : SameMaps [] []
  | cons {left right : Snapshot} {lefts rights : List Snapshot}
      (identifiers : left.identifier = right.identifier)
      (versions : left.version = right.version)
      (members : left.members.Perm right.members)
      (tail : SameMaps lefts rights) :
      SameMaps (left :: lefts) (right :: rights)

private theorem SameMaps.identifiers_equal {left right : List Snapshot}
    (h : SameMaps left right) :
    left.map Snapshot.identifier = right.map Snapshot.identifier := by
  induction h with
  | nil => rfl
  | cons hid _ _ _ ih => simp [hid, ih]

private theorem validPair_equiv (claim : Claim) (left right : Snapshot)
    (hid : left.identifier = right.identifier)
    (hver : left.version = right.version)
    (hperm : left.members.Perm right.members) :
    ValidPair claim left ↔ ValidPair claim right := by
  have hnames := hperm.map Member.name
  have hnonempty : left.members ≠ [] ↔ right.members ≠ [] := by
    constructor
    · intro hl hr
      have hp : left.members.Perm [] := by simpa [hr] using hperm
      exact hl hp.eq_nil
    · intro hr hl
      have hp : right.members.Perm [] := by simpa [hl] using hperm.symm
      exact hr hp.eq_nil
  have hevidence :
      claim.evidenceFile ∈ left.members.map Member.name ↔
        claim.evidenceFile ∈ right.members.map Member.name := hnames.mem_iff
  have hnodup : (left.members.map Member.name).Nodup ↔
      (right.members.map Member.name).Nodup := hnames.nodup_iff
  have hall :
      left.members.all (fun member =>
        decide (ValidMember left.identifier member)) = true ↔
      right.members.all (fun member =>
        decide (ValidMember right.identifier member)) = true := by
    simp only [List.all_eq_true, decide_eq_true_eq]
    constructor
    · intro h member hm
      have hleft : member ∈ left.members := hperm.mem_iff.mpr hm
      simpa [hid] using h member hleft
    · intro h member hm
      have hright : member ∈ right.members := hperm.mem_iff.mp hm
      simpa [hid] using h member hright
  constructor
  · intro h
    exact ⟨h.1.trans hver, hnonempty.mp h.2.1,
      hevidence.mp h.2.2.1, hnodup.mp h.2.2.2.1, hall.mp h.2.2.2.2⟩
  · intro h
    exact ⟨h.1.trans hver.symm, hnonempty.mpr h.2.1,
      hevidence.mpr h.2.2.1, hnodup.mpr h.2.2.2.1, hall.mpr h.2.2.2.2⟩

private theorem SameMaps.pair_checks_equal (claims : List Claim)
    {left right : List Snapshot} (h : SameMaps left right) :
    (claims.zip left).all (fun pair =>
      decide (ValidPair pair.1 pair.2)) =
    (claims.zip right).all (fun pair =>
      decide (ValidPair pair.1 pair.2)) := by
  induction h generalizing claims with
  | nil => cases claims <;> rfl
  | @cons l r ls rs hid hver hperm _ ih =>
      cases claims with
      | nil => rfl
      | cons claim rest =>
          have hp : decide (ValidPair claim l) =
              decide (ValidPair claim r) :=
            (decide_eq_decide).2 (validPair_equiv claim l r hid hver hperm)
          simp [hp, ih rest]

private theorem SameMaps.emit_equal (claims : List Claim)
    {left right : List Snapshot} (h : SameMaps left right)
    (hkeys : ∀ snapshot ∈ left,
      (snapshot.members.map Member.name).Nodup) :
    emit claims left = emit claims right := by
  induction h generalizing claims with
  | nil => cases claims <;> rfl
  | @cons l r ls rs hid hver hperm _ ih =>
      cases claims with
      | nil => rfl
      | cons claim rest =>
          have hhead : (l.members.map Member.name).Nodup :=
            hkeys l (by simp)
          have htail : ∀ snapshot ∈ ls,
              (snapshot.members.map Member.name).Nodup := by
            intro snapshot hs
            exact hkeys snapshot (by simp [hs])
          have hsort := sortMembers_perm_eq l.members r.members hperm hhead
          have hfor : emitFor l = emitFor r := by
            unfold emitFor
            rw [hsort]
            apply List.map_congr_left
            intro member _
            simp [artifactOf, hid, hver]
          change emitFor l ++ emit rest ls = emitFor r ++ emit rest rs
          rw [hfor, ih rest htail]

theorem M010_A5_deterministic_enumeration (claims : List Claim)
    {left right : List Snapshot} (hequiv : SameMaps left right)
    (hkeys : ∀ snapshot ∈ left,
      (snapshot.members.map Member.name).Nodup) :
    emit claims left = emit claims right ∧
      validate claims left = validate claims right := by
  have hemit := hequiv.emit_equal claims hkeys
  have hids := hequiv.identifiers_equal
  have hpairs := hequiv.pair_checks_equal claims
  have hvalid : ValidInput claims left ↔ ValidInput claims right := by
    unfold ValidInput
    rw [hids, hpairs, hemit]
  constructor
  · exact hemit
  · by_cases hv : ValidInput claims left
    · have hr := hvalid.mp hv
      simp [validate, hv, hr, hemit]
    · have hr : ¬ValidInput claims right := by
        intro hright
        exact hv (hvalid.mpr hright)
      simp [validate, hv, hr]

/-- Explicit rejection classes for the exact-string, unique-dictionary-key
model. `badName` covers forbidden separators, special basenames, and suffixes.
`badDigest` and `badCommit` cover syntax, not byte-content authenticity. -/
inductive Malformed (claims : List Claim) (snapshots : List Snapshot) : Prop where
  | claimStageOrder (h : claims.map Claim.profile ≠ stages) :
      Malformed claims snapshots
  | snapshotStageOrder (h : snapshots.map Snapshot.identifier ≠ stages) :
      Malformed claims snapshots
  | repeatedCommit (h : ¬(claims.map Claim.mergedCommit).Nodup) :
      Malformed claims snapshots
  | badCommit (claim : Claim) (hmem : claim ∈ claims)
      (h : validCommit claim.mergedCommit ≠ true) :
      Malformed claims snapshots
  | versionMismatch (claim : Claim) (snapshot : Snapshot)
      (hpair : (claim, snapshot) ∈ claims.zip snapshots)
      (h : claim.version ≠ snapshot.version) :
      Malformed claims snapshots
  | emptyMembers (claim : Claim) (snapshot : Snapshot)
      (hpair : (claim, snapshot) ∈ claims.zip snapshots)
      (h : snapshot.members = []) :
      Malformed claims snapshots
  | missingEvidence (claim : Claim) (snapshot : Snapshot)
      (hpair : (claim, snapshot) ∈ claims.zip snapshots)
      (h : claim.evidenceFile ∉ snapshot.members.map Member.name) :
      Malformed claims snapshots
  | repeatedMemberName (claim : Claim) (snapshot : Snapshot)
      (hpair : (claim, snapshot) ∈ claims.zip snapshots)
      (h : ¬(snapshot.members.map Member.name).Nodup) :
      Malformed claims snapshots
  | badName (claim : Claim) (snapshot : Snapshot) (member : Member)
      (hpair : (claim, snapshot) ∈ claims.zip snapshots)
      (hmember : member ∈ snapshot.members)
      (h : validName member.name ≠ true) :
      Malformed claims snapshots
  | badDigest (claim : Claim) (snapshot : Snapshot) (member : Member)
      (hpair : (claim, snapshot) ∈ claims.zip snapshots)
      (hmember : member ∈ snapshot.members)
      (h : validDigest member.digest ≠ true) :
      Malformed claims snapshots
  | forbiddenMidi (claim : Claim) (snapshot : Snapshot) (member : Member)
      (hpair : (claim, snapshot) ∈ claims.zip snapshots)
      (hmember : member ∈ snapshot.members)
      (hmid : hasMidiSuffix member.name = true)
      (hstage : snapshot.identifier ≠ firstStage) :
      Malformed claims snapshots
  | repeatedLogicalPath
      (h : ¬((emit claims snapshots).map Artifact.logicalPath).Nodup) :
      Malformed claims snapshots
  | wrongFinalStage
      (h : (emit claims snapshots).getLast?.map Artifact.stage ≠ some lastStage) :
      Malformed claims snapshots

private theorem pair_valid_of_input {claims : List Claim}
    {snapshots : List Snapshot} (h : ValidInput claims snapshots)
    (claim : Claim) (snapshot : Snapshot)
    (hpair : (claim, snapshot) ∈ claims.zip snapshots) :
    ValidPair claim snapshot := by
  obtain ⟨_, _, _, _, hpairs, _, _⟩ := h
  exact (decide_eq_true_eq).mp
    ((List.all_eq_true.mp hpairs) (claim, snapshot) hpair)

private theorem member_valid_of_input {claims : List Claim}
    {snapshots : List Snapshot} (h : ValidInput claims snapshots)
    (claim : Claim) (snapshot : Snapshot) (member : Member)
    (hpair : (claim, snapshot) ∈ claims.zip snapshots)
    (hmember : member ∈ snapshot.members) :
    ValidMember snapshot.identifier member := by
  have hpairvalid := pair_valid_of_input h claim snapshot hpair
  have hall := hpairvalid.2.2.2.2
  exact (decide_eq_true_eq).mp
    ((List.all_eq_true.mp hall) member hmember)

theorem M010_A6_fail_closed_malformed (claims : List Claim)
    (snapshots : List Snapshot) (h : Malformed claims snapshots) :
    validate claims snapshots = none := by
  have hnot : ¬ValidInput claims snapshots := by
    intro hv
    cases h with
    | claimStageOrder bad => exact bad hv.1
    | snapshotStageOrder bad => exact bad hv.2.1
    | repeatedCommit bad => exact bad hv.2.2.1
    | badCommit claim hmem bad =>
        have hall := hv.2.2.2.1
        exact bad ((List.all_eq_true.mp hall) claim hmem)
    | versionMismatch claim snapshot hpair bad =>
        exact bad (pair_valid_of_input hv claim snapshot hpair).1
    | emptyMembers claim snapshot hpair bad =>
        exact (pair_valid_of_input hv claim snapshot hpair).2.1 bad
    | missingEvidence claim snapshot hpair bad =>
        exact bad (pair_valid_of_input hv claim snapshot hpair).2.2.1
    | repeatedMemberName claim snapshot hpair bad =>
        exact bad (pair_valid_of_input hv claim snapshot hpair).2.2.2.1
    | badName claim snapshot member hpair hmember bad =>
        exact bad (member_valid_of_input hv claim snapshot member hpair hmember).1
    | badDigest claim snapshot member hpair hmember bad =>
        exact bad (member_valid_of_input hv claim snapshot member hpair hmember).2.1
    | forbiddenMidi claim snapshot member hpair hmember hmid bad =>
        exact bad
          ((member_valid_of_input hv claim snapshot member hpair hmember).2.2 hmid)
    | repeatedLogicalPath bad => exact bad hv.2.2.2.2.2.1
    | wrongFinalStage bad => exact bad hv.2.2.2.2.2.2
  simp [validate, hnot]

private def demoCommitPrefix : String :=
  "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

private def demoDigest : String :=
  "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

private def demoAudit : Member :=
  {name := "audit.json", digest := demoDigest}

private def demoExtra : Member :=
  {name := "extra.json", digest := demoDigest}

def demoClaims : List Claim :=
  stages.map (fun stage => {
    profile := stage,
    version := "v",
    mergedCommit := demoCommitPrefix ++ stage.takeRight 3,
    evidenceFile := "audit.json"
  })

def demoSnapshots : List Snapshot :=
  stages.map (fun stage => {
    identifier := stage,
    version := "v",
    members := [demoAudit]
  })

def demoSnapshotsExtra : List Snapshot :=
  stages.map (fun stage => {
    identifier := stage,
    version := "v",
    members := if stage = firstStage then
      [demoExtra, demoAudit]
    else [demoAudit]
  })

private theorem demo_two_sorted :
    sortMembers [demoExtra, demoAudit] = [demoAudit, demoExtra] := by
  have hperm : [demoExtra, demoAudit].Perm [demoAudit, demoExtra] :=
    List.Perm.swap _ _ []
  have hkeys : (([demoExtra, demoAudit] : List Member).map Member.name).Nodup := by
    decide
  rw [sortMembers_perm_eq _ _ hperm hkeys]
  unfold sortMembers
  apply List.mergeSort_of_sorted
  decide

private theorem demo_paths_base :
    (emit demoClaims demoSnapshots).map Artifact.logicalPath = [
      "dist/mat-spec-001/audit.json", "dist/mat-spec-002/audit.json",
      "dist/mat-spec-003/audit.json", "dist/mat-spec-004/audit.json",
      "dist/mat-spec-005/audit.json", "dist/mat-spec-006/audit.json",
      "dist/mat-spec-007/audit.json", "dist/mat-spec-008/audit.json",
      "dist/mat-spec-009/audit.json"
    ] := by
  simp [emit, demoClaims, demoSnapshots, stages, emitFor, sortMembers,
    demoAudit, artifactOf, logicalPath, stageSuffix, String.push]

private theorem demo_paths_extra :
    (emit demoClaims demoSnapshotsExtra).map Artifact.logicalPath = [
      "dist/mat-spec-001/audit.json", "dist/mat-spec-001/extra.json",
      "dist/mat-spec-002/audit.json", "dist/mat-spec-003/audit.json",
      "dist/mat-spec-004/audit.json", "dist/mat-spec-005/audit.json",
      "dist/mat-spec-006/audit.json", "dist/mat-spec-007/audit.json",
      "dist/mat-spec-008/audit.json", "dist/mat-spec-009/audit.json"
    ] := by
  have hs :
      ([{name := "extra.json", digest := demoDigest},
        {name := "audit.json", digest := demoDigest}] : List Member).mergeSort memberLE =
      [{name := "audit.json", digest := demoDigest},
       {name := "extra.json", digest := demoDigest}] := by
    simpa [sortMembers, demoAudit, demoExtra] using demo_two_sorted
  simp [emit, demoClaims, demoSnapshotsExtra, stages, emitFor,
    sortMembers, hs, demoAudit, demoExtra, memberLE,
    artifactOf, logicalPath, stageSuffix, firstStage, String.push]

private theorem demo_last_base :
    (emit demoClaims demoSnapshots).getLast?.map Artifact.stage = some lastStage := by
  simp [emit, demoClaims, demoSnapshots, stages, emitFor, sortMembers,
    artifactOf, lastStage]

private theorem demo_last_extra :
    (emit demoClaims demoSnapshotsExtra).getLast?.map Artifact.stage =
      some lastStage := by
  simp [emit, demoClaims, demoSnapshotsExtra, stages, emitFor, sortMembers,
    artifactOf, lastStage, firstStage]

theorem M010_A7_accepted_and_rejected_nonvacuity :
    (validate demoClaims demoSnapshots).isSome = true ∧
    (validate demoClaims demoSnapshotsExtra).isSome = true ∧
    (validate demoClaims []).isNone = true := by
  have hbase : ValidInput demoClaims demoSnapshots := by
    unfold ValidInput
    refine ⟨by decide, by decide, by decide, by decide, by decide, ?_, ?_⟩
    · rw [demo_paths_base]
      decide
    · exact demo_last_base
  have hextra : ValidInput demoClaims demoSnapshotsExtra := by
    unfold ValidInput
    refine ⟨by decide, by decide, by decide, by decide, by decide, ?_, ?_⟩
    · rw [demo_paths_extra]
      decide
    · exact demo_last_extra
  have hbad : ¬ValidInput demoClaims [] := by
    intro h
    have hstages := h.2.1
    simp [stages] at hstages
  simp [validate, hbase, hextra, hbad]

end MAT010.Archive
