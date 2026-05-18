import WillardTopology.Basic
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_1_Sets

-- Def1_2: Elementary set calculus

/--
Definition 1.2 (Elementary set calculus).

If `A` and `B` are sets and every element of `A` is an element of `B`,
we write `A ⊂ B` or `B ⊃ A` and say `A` is a *subset* of `B` or `B` *contains* `A`.
-/
def subset {α : Type u} (A B : Set α) : Prop :=
  ∀ x, x ∈ A → x ∈ B

/--
The collection `P(A)` of all subsets of a given set `A`, is called the *power set* of `A`.
-/
def powerset {α : Type u} (A : Set α) : Set (Set α) :=
  fun S => subset S A

/--
We say sets `A` and `B` are *equal*, `A = B`, when both `A ⊂ B` and `B ⊂ A`.
Evidently, `A` and `B` are equal iff they have the same elements.
-/
def setEqual {α : Type u} (A B : Set α) : Prop :=
  subset A B ∧ subset B A

/--
We write `B ∖ A` to denote the set `{x ∈ B | x ∉ A}`. `B ∖ A` is called the
*complement* of `B` in `A`.
-/
def setDifference {α : Type u} (A B : Set α) : Set α :=
  def1_1_sets_setFilter B (fun x => x ∉ A)

/--
The *empty set*, `∅`, is the set having no elements. By the criterion for equality
of sets, there is only one empty set and, by the criterion for containment, it is a
subset of every other set.
-/
def emptySet {α : Type u} : Set α :=
  fun _ => False
