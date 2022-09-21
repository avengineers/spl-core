from typing import List

from src.creator.variant import Variant


class SplProject:
    def __init__(self, parent, name: str, variants: List[Variant]):
        self.parent = parent
        self.name = name
        self.variants = variants
