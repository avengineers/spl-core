from pathlib import Path

from spl_core.project_creator.variant import Variant


class WorkspaceArtifacts:
    def __init__(self, project_root_dir: Path):
        self.workspace_root_dir = project_root_dir
        self.variants_dir = self.root_dir.joinpath("variants")
        self.src_dir = self.root_dir.joinpath("src")
        self.test_dir = self.root_dir.joinpath("test")
        self.components_dir = self.root_dir.joinpath("components")

    @property
    def root_dir(self) -> Path:
        return self.workspace_root_dir

    @property
    def build_script(self) -> Path:
        return self.root_dir.joinpath("build.bat")

    @property
    def kconfig_model_file(self) -> Path:
        return self.root_dir.joinpath("KConfig")

    def get_build_dir(self, variant: Variant, build_kit: str) -> Path:
        return self.root_dir.joinpath(f"build/{variant}/{build_kit}")

    def get_variant_dir(self, variant: Variant) -> Path:
        return self.variants_dir.joinpath(f"{variant.flavor}/{variant.subsystem}")

    def get_component_path(self, component_name: str) -> Path:
        return self.components_dir.joinpath(component_name)

    def get_kconfig_config_file(self, variant: Variant) -> Path:
        return self.get_variant_dir(variant).joinpath("config.txt")
