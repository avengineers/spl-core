import json
import subprocess
from subprocess import CompletedProcess
from unittest.mock import patch

from src.creator.creator import ProjectGenerator, main, Variant
from src.creator.project_artifacts import ProjectArtifacts
from tests.utils import TestUtils


def execute_command(command: str) -> CompletedProcess:
    return subprocess.run(command.split())


class TestProjectGenerator:
    def test_materialize(self):
        out_dir = TestUtils.create_clean_test_dir('test_materialize')
        project_name = 'MyProject'
        project_dir = ProjectGenerator(project_name, [Variant('Flv1', 'Sys1'), Variant('Flv1', 'Sys2')]) \
            .materialize(out_dir.path)

        assert project_dir == out_dir.joinpath(project_name)
        assert project_dir.joinpath('CMakeLists.txt').exists()
        assert project_dir.joinpath('variants/Flv1/Sys1/config.cmake').exists()
        assert project_dir.joinpath('variants/Flv1/Sys2/config.cmake').exists()
        cmake_variants_file = project_dir.joinpath(
            '.vscode/cmake-variants.json')
        assert cmake_variants_file.exists()
        cmake_variants_text = cmake_variants_file.read_text().strip()
        "There shall not be any empty lines in resulting json file."
        assert '' not in cmake_variants_text.replace('\r\n', '\n').split('\n')
        cmake_variants_json = json.loads(cmake_variants_text)
        assert len(cmake_variants_json['variant']['choices']) == 2
        assert 'Flv1/Sys1' in cmake_variants_json['variant']['choices']
        assert 'Flv1/Sys2' in cmake_variants_json['variant']['choices']
        assert 'Flv1/Sys3' not in cmake_variants_json['variant']['choices']
        assert 'flavor/subsystem' not in cmake_variants_json['variant']['choices']
        assert cmake_variants_json['variant']['default'] == 'Flv1/Sys1'

    def test_create_project_running_main(self):
        out_dir = TestUtils.create_clean_test_dir('test_create_project_running_main')
        with patch('sys.argv', [
            'some_name',
            '--name', 'MyProject1',
            '--variant', 'Flv1/Sys1',
            '--variant', 'Flv1/Sys2',
            '--out_dir', f"{out_dir.path}"
        ]):
            main()

        project_dir = out_dir.joinpath('MyProject1')
        project_artifacts = ProjectArtifacts(project_dir)
        assert project_dir.joinpath('CMakeLists.txt').exists()
        assert project_dir.joinpath('variants/Flv1/Sys1/config.cmake').exists()
        assert project_dir.joinpath('variants/Flv1/Sys2/config.cmake').exists()

        result = execute_command(f"{project_artifacts.build_script} -build -target selftests -installMandatory")
        assert result.returncode == 0

    def test_create_project_description(self):
        project_description = ProjectGenerator.create_project_description('SomeProject', [Variant('Flv1', 'Sys1'),
                                                                                          Variant('Flv1', 'Sys2')])
        assert project_description == {
            "name": "SomeProject",
            "variants": {
                "0": {
                    "flavor": "Flv1",
                    "subsystem": "Sys1"
                },
                "1": {
                    "flavor": "Flv1",
                    "subsystem": "Sys2"
                }
            }
        }
