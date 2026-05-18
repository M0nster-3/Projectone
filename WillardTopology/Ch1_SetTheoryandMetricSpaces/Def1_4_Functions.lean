import WillardTopology.Basic
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_1_Sets
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_2_Elementary_set_calculus

/-- Definition 1.4 (Functions). A *function* (or *map*) `f` from a set `A` to a set `B` is a rule
which assigns to `a ∈ A` a unique `f a ∈ B`. `A` is the *domain* and `B` the *codomain* (or *range*)
of `f`. `f` is sometimes written `A → f → B` or `f : A → B`. -/
def def1_4_function {α β : Type u} (f : α → β) (A : Set α) (B : Set β) : Prop :=
  ∀ a, a ∈ A → f a ∈ B

/-- For `f` and `g` mapping `A` to `B`, if `f a = g a` for all `a ∈ A`, then `f = g`.
Otherwise there exists `b` such that `f b ≠ g b`. -/
theorem def1_4_function_extensionality {α β : Type u} {f g : α → β} {A : Set α} {B : Set β}
    (h : ∀ a, a ∈ A → f a = g a) : f = g :=
  sorry
