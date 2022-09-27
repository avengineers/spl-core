import argparse
import dataclasses
import logging
from pathlib import Path
from typing import Dict, List

from cookiecutter.main import cookiecutter

from src.common.common import existing_path
from src.creator.project_artifacts import ProjectArtifacts


@dataclasses.dataclass
class Variant:
    flavor: str
    subsystem: str

    @classmethod
    def from_string(cls, variant: str):
        return cls(*variant.split('/'))


class ProjectGenerator:
    def __init__(self, name: str, variants: List[Variant]):
        self.logger = logging.getLogger(__name__)
        self.project_description = self.create_project_description(name, variants)

    @staticmethod
    def create_project_description(name: str, variants: List[Variant]) -> Dict:
        project_description = {'name': name, 'variants': {}}
        for index, variant in enumerate(variants):
            project_description['variants'][f"{index}"] = {
                'flavor': variant.flavor,
                'subsystem': variant.subsystem
            }
        return project_description

    @property
    def project_template_path(self) -> Path:
        return Path(__file__).parent.joinpath('templates/project')

    @property
    def variant_template_path(self) -> Path:
        return Path(__file__).parent.joinpath('templates/variant')

    @property
    def project_name(self) -> str:
        return self.project_description['name']

    def materialize(self, out_dir: Path) -> Path:
        project_artifacts = ProjectArtifacts(out_dir.joinpath(self.project_name))
        result_path = cookiecutter(str(self.project_template_path),
                                   output_dir=f"{out_dir}",
                                   no_input=True,
                                   extra_context=self.project_description)
        for variant in self.project_description['variants'].values():
            self.add_variant(variant, project_artifacts.variants_dir)
        self.logger.info(f"Project created under: {result_path}")
        return Path(result_path)

    def add_variant(self, variant_description: Dict, out_dir: Path):
        result_path = cookiecutter(str(self.variant_template_path),
                                   output_dir=f"{out_dir}",
                                   no_input=True,
                                   extra_context=variant_description,
                                   overwrite_if_exists=True)
        self.logger.info(f"Variant created under: {result_path}")
        return Path(result_path)


def main():
    parser = argparse.ArgumentParser(description='Project creator')
    parser.add_argument('--name', required=True, type=str,
                        help="Project name. A directory with this name will be created in the <out_dir>.")
    parser.add_argument('--variant', required=True, action='append', type=Variant.from_string,
                        help="Variant name as <flavor>/<subsystem>. E.g. FLV1/SYS1. This option can be used multiple times.")
    parser.add_argument('--out_dir', required=True, type=existing_path,
                        help="Target directory where the project folder will be created.")
    arguments = parser.parse_args()
    ProjectGenerator(arguments.name, arguments.variant).materialize(arguments.out_dir)


if __name__ == '__main__':
    main()
