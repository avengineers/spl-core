from pathlib import Path

from src.creator.variant import Variant


class ProjectArtifacts:
    def __init__(self, project_root_dir: Path):
        self.project_root_dir = project_root_dir
        self.variants_dir = self.root_dir.joinpath('variants')
        self.src_dir = self.root_dir.joinpath('src')
        self.test_dir = self.root_dir.joinpath('test')

    @property
    def root_dir(self) -> Path:
        return self.project_root_dir

    @property
    def build_script(self) -> Path:
        return self.root_dir.joinpath('build.bat')

    def get_build_dir(self, variant: Variant, build_kit: str) -> Path:
        return self.root_dir.joinpath(f"build/{variant}/{build_kit}")

    def get_variant_dir(self, variant: Variant) -> Path:
        return self.variants_dir.joinpath(f"{variant.flavor}/{variant.subsystem}")
