import WillardTopology.Basic
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_1_Sets

-- Indexed union: ⋃_{i} B_i = {x | ∃ i, x ∈ B_i}
def iUnion {α ι : Type u} (B : ι → Set α) : Set α := fun x => ∃ i, x ∈ B i

-- Indexed intersection: ⋂_{i} B_i = {x | ∀ i, x ∈ B_i}
def iInter {α ι : Type u} (B : ι → Set α) : Set α := fun x => ∀ i, x ∈ B i

-- Binary union: A ∪ B = {x | x ∈ A ∨ x ∈ B}
def union {α : Type u} (A B : Set α) : Set α := fun x => x ∈ A ∨ x ∈ B

-- Binary intersection: A ∩ B = {x | x ∈ A ∧ x ∈ B}
def inter {α : Type u} (A B : Set α) : Set α := fun x => x ∈ A ∧ x ∈ B

-- Theorem 1.10 (a): ⋃_i (B_i ∪ C_i) = (⋃_i B_i) ∪ (⋃_i C_i)
theorem thm_1_10_a {α ι : Type u} (B C : ι → Set α) :
    iUnion (fun i => union (B i) (C i)) = union (iUnion B) (iUnion C) := by
  funext x
  simp [iUnion, union]
  constructor
  · rintro ⟨i, (hB | hC)⟩
    · exact Or.inl ⟨i, hB⟩
    · exact Or.inr ⟨i, hC⟩
  · rintro (⟨i, hB⟩ | ⟨i, hC⟩)
    · exact ⟨i, Or.inl hB⟩
    · exact ⟨i, Or.inr hC⟩

-- Theorem 1.10 (b): ⋂_j (B_j ∩ C_j) = (⋂_j B_j) ∩ (⋂_j C_j)
theorem thm_1_10_b {α ι : Type u} (B C : ι → Set α) :
    iInter (fun i => inter (B i) (C i)) = inter (iInter B) (iInter C) := by
  funext x
  simp [iInter, inter]
  constructor
  · intro h
    exact ⟨fun i => (h i).1, fun i => (h i).2⟩
  · rintro ⟨hB, hC⟩ i
    exact ⟨hB i, hC i⟩

-- Theorem 1.10 (c): distributive laws
-- A ∩ (⋃_i B_i) = ⋃_i (A ∩ B_i)
theorem thm_1_10_c_union {α ι : Type u} (A : Set α) (B : ι → Set α) :
    inter A (iUnion B) = iUnion (fun i => inter A (B i)) := by
  funext x
  simp [inter, iUnion]
  constructor
  · rintro ⟨hA, i, hBi⟩; exact ⟨i, hA, hBi⟩
  · rintro ⟨i, hA, hBi⟩; exact ⟨hA, i, hBi⟩

-- A ∪ (⋂_j C_j) = ⋂_j (A ∪ C_j)
theorem thm_1_10_c_inter {α κ : Type u} (A : Set α) (C : κ → Set α) :
    union A (iInter C) = iInter (fun j => union A (C j)) := by
  funext x
  simp [union, iInter]
  constructor
  · rintro (hA | hAll) j
    · exact Or.inl hA
    · exact Or.inr (hAll j)
  · intro h
    by_cases hA : x ∈ A
    · exact Or.inl hA
    · exact Or.inr (fun j => (h j).resolve_left hA)

-- Theorem 1.10 (d): (⋃_i B_i) ∩ (⋂_j C_j) = ⋃_i (B_i ∩ ⋂_j C_j) = ⋂_j (⋃_i B_i ∩ C_j)
theorem thm_1_10_d {α ι κ : Type u} [Nonempty κ] (B : ι → Set α) (C : κ → Set α) :
    inter (iUnion B) (iInter C) = iUnion (fun i => inter (B i) (iInter C)) ∧
    iUnion (fun i => inter (B i) (iInter C)) = iInter (fun j => inter (iUnion B) (C j)) := by
  have hne : Nonempty κ := by infer_instance
  obtain ⟨j₀⟩ := hne
  have h1 : inter (iUnion B) (iInter C) = iUnion (fun i => inter (B i) (iInter C)) := by
    funext x
    simp [inter, iUnion]
    constructor
    · rintro ⟨⟨i, hBi⟩, hAll⟩; exact ⟨i, hBi, hAll⟩
    · rintro ⟨i, hBi, hAll⟩; exact ⟨⟨i, hBi⟩, hAll⟩
  have h2 : iUnion (fun i => inter (B i) (iInter C)) = iInter (fun j => inter (iUnion B) (C j)) := by
    funext x
    simp [iUnion, iInter]
    constructor
    · rintro ⟨i, hBi, hAll⟩ j; exact ⟨⟨i, hBi⟩, hAll j⟩
    · intro h
      rcases (h j₀).1 with ⟨i, hBi⟩
      exact ⟨i, hBi, fun j => (h j).2⟩
  exact And.intro h1 h2
