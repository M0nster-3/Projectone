import WillardTopology.Basic
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_5_Relations
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_6_Order_relations

-- Def1_7: Lattices



/-- If A is a partially ordered set, a *minimal element* of A is an element m₀ ∈ A
    such that a < m₀ does not hold for any a ∈ A. -/
def def1_7_isMinimal {α : Type u} (m₀ : α) (R : Set (α × α)) (A : Set α) : Prop :=
  m₀ ∈ A ∧ ∀ a, a ∈ A → ¬ def1_6_strictFromPartial R a m₀

/-- An *upper bound* of a subset B of A is an element u ∈ A such that b ≤ u for all b ∈ B. -/
def def1_7_isUpperBound {α : Type u} (u : α) (R : Set (α × α)) (A B : Set α) : Prop :=
  u ∈ A ∧ ∀ b, b ∈ B → def1_5_related R b u

/-- A *lower bound* of a subset B of A is an element l ∈ A such that l ≤ b for all b ∈ B. -/
def def1_7_isLowerBound {α : Type u} (l : α) (R : Set (α × α)) (A B : Set α) : Prop :=
  l ∈ A ∧ ∀ b, b ∈ B → def1_5_related R l b

/-- The *least upper bound* (lub) of a subset B of A is the smallest upper bound of B if it exists. -/
def def1_7_isLUB {α : Type u} (s : α) (R : Set (α × α)) (A B : Set α) : Prop :=
  def1_7_isUpperBound s R A B ∧ ∀ u, def1_7_isUpperBound u R A B → def1_5_related R s u

/-- The *greatest lower bound* (glb) of a subset B of A is the largest lower bound of B if it exists. -/
def def1_7_isGLB {α : Type u} (s : α) (R : Set (α × α)) (A B : Set α) : Prop :=
  def1_7_isLowerBound s R A B ∧ ∀ l, def1_7_isLowerBound l R A B → def1_5_related R l s

/-- A *lattice* is a partially ordered set L in which each two-element set {a, b} in L
    has a least upper bound a ∨ b and a greatest lower bound a ∧ b. -/
def def1_7_isLattice {α : Type u} (R : Set (α × α)) (L : Set α) : Prop :=
  def1_6_isPartialOrder R L ∧
  ∀ a b, a ∈ L → b ∈ L →
    (∃ lub, def1_7_isLUB lub R L (fun x => x = a ∨ x = b)) ∧
    (∃ glb, def1_7_isGLB glb R L (fun x => x = a ∨ x = b))

/-- A *lattice having 0 and 1* (or *bounded lattice*) is a lattice L
    with a least element 0 (0 ≤ a for each a ∈ L) and a greatest element 1 (a ≤ 1 for each a ∈ L). -/
def def1_7_isBoundedLattice {α : Type u} (R : Set (α × α)) (L : Set α) : Prop :=
  def1_7_isLattice R L ∧
  (∃ zero, def1_6_isSmallest zero R L) ∧
  (∃ one, def1_6_isLargest one R L)
