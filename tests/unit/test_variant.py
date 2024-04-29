from spl_core.project_creator.variant import Variant


class TestVariant:
    def test_from_string(self):
        assert Variant.from_string("Bla/Blub") == Variant("Bla/Blub")

    def test_lt(self):
        assert Variant("A") < Variant("B")
        assert Variant("B") > Variant("A")
        assert Variant("1") < Variant("A")
        assert Variant("2") > Variant("1")

    def test_vars(self):
        assert vars(Variant("A")) == {"name": "A"}

    def test_hash(self):
        assert Variant("A") in [Variant("B"), Variant("A")]
        assert list({Variant("C"), Variant("B")} - {Variant("B")}) == [Variant("C")]
