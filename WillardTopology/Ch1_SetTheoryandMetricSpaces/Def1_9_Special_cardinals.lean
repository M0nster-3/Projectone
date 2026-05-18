import WillardTopology.Basic
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_8_Cardinality

opaque Real : Type

/-- The empty set is the cardinal `0`, and the cardinal number `n`
    is the set `{0, 1, …, n-1}`. -/
def finiteCardinal (n : Nat) : Set Nat :=
  fun k => k < n

/-- A set `A` is *denumerable* if `A` is equipotent with `ℕ`;
    in this case we write `|A| = ℵ₀`. -/
def denumerable {α : Type} (A : Set α) : Prop :=
  equipotent A (fun (_ : Nat) => True)

/-- A set `A` is said to have the *cardinal of the continuum*
    if `A` is equipotent with `ℝ`; then we write `|A| = 𝔠`. -/
def hasCardinalOfContinuum {α : Type} (A : Set α) : Prop :=
  equipotent A (fun (_ : Real) => True)

/-- A set `A` is *countable* iff `A` is denumerable or has cardinal number `n`
    for some `n = 0, 1, 2, …`; otherwise, `A` is *uncountable*. -/
def countable {α : Type} (A : Set α) : Prop :=
  denumerable A ∨ ∃ n : Nat, equipotent A (finiteCardinal n)

/-- A set `A` is *uncountable* iff it is not countable. -/
def uncountable {α : Type} (A : Set α) : Prop :=
  ¬ countable A
