import WillardTopology.Basic
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_1_Sets
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_2_Elementary_set_calculus
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_5_Relations

-- Def1_6: Order relations

/-- A relation R on a set A is a *partial order* provided R is reflexive, antisymmetric and transitive. -/
def def1_6_isPartialOrder {α : Type u} (R : Set (α × α)) (A : Set α) : Prop :=
  def1_5_reflexive R A ∧ def1_5_antisymmetric R ∧ def1_5_transitive R

/-- In the context of a partial order ≤, a < b is defined by a ≤ b and a ≠ b. -/
def def1_6_strictFromPartial {α : Type u} (R : Set (α × α)) (a b : α) : Prop :=
  def1_5_related R a b ∧ a ≠ b

/-- A strict order is a transitive relation with the property that for any a and b, if a < b then b ≮ a. -/
def def1_6_isStrictOrder {α : Type u} (R : Set (α × α)) : Prop :=
  def1_5_transitive R ∧ (∀ a b, def1_5_related R a b → ¬ def1_5_related R b a)

/-- Any strict order < determines a partial order ≤ defined by a ≤ b iff a < b or a = b. -/
def def1_6_partialFromStrict {α : Type u} (R : Set (α × α)) (a b : α) : Prop :=
  def1_5_related R a b ∨ a = b

/-- A set A is *linearly ordered* by a partial order ≤ provided that for any a, b ∈ A
exactly one of a < b, b < a, or a = b holds.

The "exactly one" follows from antisymmetry: only the trichotomy (at least one holds) needs stating. -/
def def1_6_isLinearOrder {α : Type u} (R : Set (α × α)) (A : Set α) : Prop :=
  def1_6_isPartialOrder R A ∧ (∀ a b, a ∈ A → b ∈ A →
    (def1_6_strictFromPartial R a b ∨ def1_6_strictFromPartial R b a ∨ a = b))

/-- The *smallest element* of A, if it exists, is the element a₀ such that a₀ ≤ a for each a ∈ A. -/
def def1_6_isSmallest {α : Type u} (a₀ : α) (R : Set (α × α)) (A : Set α) : Prop :=
  a₀ ∈ A ∧ ∀ a, a ∈ A → def1_5_related R a₀ a

/-- The *largest element* of A, if it exists, is the element a₁ such that a ≤ a₁ for each a ∈ A. -/
def def1_6_isLargest {α : Type u} (a₁ : α) (R : Set (α × α)) (A : Set α) : Prop :=
  a₁ ∈ A ∧ ∀ a, a ∈ A → def1_5_related R a a₁

/-- A set A is *well-ordered* if it has a linear order ≤ such that every subset of A has a smallest element. -/
def def1_6_isWellOrdered {α : Type u} (A : Set α) (R : Set (α × α)) : Prop :=
  def1_6_isLinearOrder R A ∧ (∀ B, subset B A → ((∃ x, x ∈ B) → ∃ a₀, def1_6_isSmallest a₀ R B))
