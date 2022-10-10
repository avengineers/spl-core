import logging
from pathlib import Path


class Component:
    def __init__(self, component_name: str, out_dir: Path = None):
        self.logger = logging.getLogger(__name__)
        self.name = component_name
        self.out_dir = out_dir.absolute() if out_dir else None

    @classmethod
    def from_folder(cls, component_dir: Path):
        """ This can be used by external components to also specify their location. """
        return cls(component_dir.name, component_dir.parent)
