import WillardTopology.Basic
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_1_Sets

-- Def1_5: Relations

/--
A relation R on a set A is any subset R ⊂ A × A.
(Thus every function from A to A is a relation on A, but not all relations on A
have the properties of functions.)
-/
def def1_5_isRelationOn {α : Type u} (R : Set (α × α)) (A : Set α) : Prop :=
  ∀ p, p ∈ R → p.1 ∈ A ∧ p.2 ∈ A

/--
If aRb, we also say that a is related to b.
-/
def def1_5_related {α : Type u} (R : Set (α × α)) (a b : α) : Prop :=
  (a, b) ∈ R

/--
A relation R on A is called reflexive iff aRa for each a ∈ A.
-/
def def1_5_reflexive {α : Type u} (R : Set (α × α)) (A : Set α) : Prop :=
  ∀ a, a ∈ A → def1_5_related R a a

/--
A relation R on A is called symmetric iff aRb implies bRa for all a, b.
-/
def def1_5_symmetric {α : Type u} (R : Set (α × α)) : Prop :=
  ∀ a b, def1_5_related R a b → def1_5_related R b a

/--
A relation R on A is called antisymmetric iff aRb and bRa implies a = b.
-/
def def1_5_antisymmetric {α : Type u} (R : Set (α × α)) : Prop :=
  ∀ a b, def1_5_related R a b → def1_5_related R b a → a = b

/--
A relation R on A is called transitive iff aRb and bRc implies aRc for all a, b, c.
-/
def def1_5_transitive {α : Type u} (R : Set (α × α)) : Prop :=
  ∀ a b c, def1_5_related R a b → def1_5_related R b c → def1_5_related R a c

/--
An equivalence relation on A is a reflexive, symmetric and transitive relation on A.
-/
def def1_5_equivalenceRelation {α : Type u} (R : Set (α × α)) (A : Set α) : Prop :=
  def1_5_reflexive R A ∧ def1_5_symmetric R ∧ def1_5_transitive R

/--
If R is an equivalence relation on A, the equivalence class (or R-equivalence class
when confusion is possible) of a ∈ A is the set [a] = {a' ∈ A | a'Ra}.
-/
def def1_5_equivalenceClass {α : Type u} (R : Set (α × α)) (A : Set α) (a : α) : Set α :=
  def1_1_sets_setFilter A (fun a' => def1_5_related R a' a)
