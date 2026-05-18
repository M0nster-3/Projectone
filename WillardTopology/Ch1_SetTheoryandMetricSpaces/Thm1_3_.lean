import WillardTopology.Basic
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_2_Elementary_set_calculus
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Thm1_10_

open Classical

-- Theorem 1.3 (a): 𝒰 ∖ ∅ = 𝒰 and 𝒰 ∖ 𝒰 = ∅ (De Morgan's laws)
theorem thm_1_3_a {α : Type u} (U : Set α) :
    setDifference emptySet U = U ∧ setDifference U U = emptySet := by
  have h1 : setDifference emptySet U = U := by
    apply funext; intro x
    apply propext
    dsimp [setDifference, def1_1_sets_setFilter, emptySet]
    exact ⟨fun ⟨h, _⟩ => h, fun h => ⟨h, id⟩⟩
  have h2 : setDifference U U = emptySet := by
    apply funext; intro x
    apply propext
    dsimp [setDifference, def1_1_sets_setFilter, emptySet]
    exact ⟨fun ⟨h, hn⟩ => hn h, False.elim⟩
  exact ⟨h1, h2⟩

-- Theorem 1.3 (b): 𝒰 ∖ ⋃_i B_i = ⋂_i (𝒰 ∖ B_i)
theorem thm_1_3_b {α ι : Type u} [Nonempty ι] (U : Set α) (B : ι → Set α) :
    setDifference (iUnion B) U = iInter (fun i => setDifference (B i) U) := by
  apply funext; intro x
  apply propext
  dsimp [setDifference, def1_1_sets_setFilter, iUnion, iInter]
  constructor
  · rintro ⟨hxU, hxniU⟩ i
    exact ⟨hxU, fun hxBi => hxniU ⟨i, hxBi⟩⟩
  · intro h
    let i₀ : ι := Classical.choice (inferInstance : Nonempty ι)
    have hxU := (h i₀).1
    have hxniU : ¬ (∃ i, B i x) := by
      rintro ⟨i, hxBi⟩
      exact (h i).2 hxBi
    exact ⟨hxU, hxniU⟩

-- Theorem 1.3 (c): 𝒰 ∖ ⋂_j C_j = ⋃_j (𝒰 ∖ C_j) (distributive laws)
theorem thm_1_3_c {α κ : Type u} (U : Set α) (C : κ → Set α) :
    setDifference (iInter C) U = iUnion (fun j => setDifference (C j) U) := by
  apply funext; intro x
  apply propext
  dsimp [setDifference, def1_1_sets_setFilter, iInter, iUnion]
  constructor
  · rintro ⟨hxU, hxniC⟩
    have h_exists : ∃ j, ¬ C j x :=
      byContradiction (fun h_noexists : ¬ ∃ j, ¬ C j x =>
        hxniC (fun j =>
          byContradiction (fun h_notCj : ¬ C j x =>
            h_noexists ⟨j, h_notCj⟩)))
    rcases h_exists with ⟨j, hj⟩
    exact ⟨j, hxU, hj⟩
  · rintro ⟨j, hxU, hj⟩
    exact ⟨hxU, fun hxIC => hj (hxIC j)⟩

-- Theorem 1.3 (d): (A ∪ ⋃_i B_i) ∩ ⋂_j C_j = (A ∩ ⋂_j C_j) ∪ (⋃_i B_i ∩ ⋂_j C_j)
theorem thm_1_3_d {α ι κ : Type u} (A : Set α) (B : ι → Set α) (C : κ → Set α) :
    inter (union A (iUnion B)) (iInter C) = union (inter A (iInter C)) (inter (iUnion B) (iInter C)) := by
  apply funext; intro x
  apply propext
  dsimp [inter, union, iUnion, iInter]
  constructor
  · rintro ⟨(hxA | hxIU), hxIC⟩
    · exact Or.inl ⟨hxA, hxIC⟩
    · exact Or.inr ⟨hxIU, hxIC⟩
  · rintro (⟨hxA, hxIC⟩ | ⟨hxIU, hxIC⟩)
    · exact ⟨Or.inl hxA, hxIC⟩
    · exact ⟨Or.inr hxIU, hxIC⟩
