import dataclasses


@dataclasses.dataclass
class Variant:
    flavor: str
    subsystem: str

    @classmethod
    def from_string(cls, variant: str) -> "Variant":
        return cls(*variant.split("/"))

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self, delimiter: str = "/") -> str:
        return f"{self.flavor}{delimiter}{self.subsystem}"

    def __lt__(self, other: "Variant") -> bool:
        return f"{self}" < f"{other}"

    def __hash__(self) -> int:
        return hash(f"{self}")
