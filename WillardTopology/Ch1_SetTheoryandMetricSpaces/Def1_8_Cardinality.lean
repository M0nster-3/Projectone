import WillardTopology.Basic
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_4_Functions
import WillardTopology.Ch1_SetTheoryandMetricSpaces.Def1_6_Order_relations

instance {α : Type u} : Nonempty (Set α) := ⟨fun _ => True⟩

/-- A function `f` is *one-one* (injective) on a set `A` if `f x = f y` implies `x = y`
    for all `x, y ∈ A`. -/
def isOneOneOn {α β : Type u} (f : α → β) (A : Set α) : Prop :=
  ∀ x y, x ∈ A → y ∈ A → f x = f y → x = y

/-- A function `f` maps `A` *onto* `B` if it maps `A` into `B` and every element of `B`
    has a preimage in `A`. -/
def isOnto {α β : Type u} (f : α → β) (A : Set α) (B : Set β) : Prop :=
  def1_4_function f A B ∧ ∀ b, b ∈ B → ∃ a, a ∈ A ∧ f a = b

/-- Definition 1.8: `A` is *equipotent* with `B` iff there is a one-one function from
    `A` onto `B`. -/
def equipotent {α β : Type u} (A : Set α) (B : Set β) : Prop :=
  ∃ f, isOneOneOn f A ∧ isOnto f A B

/-- Cardinal numbers are postulated to exist as sets, so chosen that every set `A`
    is equipotent with precisely one cardinal number, called the *cardinal number* of `A`
    and denoted `|A|`. -/
opaque card {α : Type u} (A : Set α) : Set α

/-- Cardinality notation `|A|`. -/
prefix:max "|" => card

/-- For cardinal numbers `C` and `D`, `C ≤ D` iff there is a one-one function
    `f : C → D`. Since cardinal numbers are sets, this is defined on `Set α`. -/
def cardLe {α : Type u} (C D : Set α) : Prop :=
  ∃ f : α → α, isOneOneOn f C ∧ def1_4_function f C D
