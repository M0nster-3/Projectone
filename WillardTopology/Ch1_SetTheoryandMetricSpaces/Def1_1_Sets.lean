import WillardTopology.Basic

def Set (α : Type u) : Type u := α → Prop

instance {α : Type u} : Membership α (Set α) where
  mem s a := s a

-- Def1_1: Sets

/--
Definition 1.1 (Sets).

A *set*, *family* or *collection* is an aggregate of things, called the *elements* or
*points* of the set. If `a` is an element of the set `A` we write `a ∈ A` and if this is
false we write `a ∉ A`.

If `A` is a set and `S` is a statement which applies to some of the elements of `A`, the
set of elements of `A` for which `S(a)` is true is denoted `{a ∈ A | S(a)}`.

The set of elements `a` in `A` for which statement `S` holds: `{a ∈ A | S a}`.
-/
def def1_1_sets_setFilter {α : Type u} (A : Set α) (S : α → Prop) : Set α :=
  fun a => a ∈ A ∧ S a
