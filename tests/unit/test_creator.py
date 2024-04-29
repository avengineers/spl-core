import json
import subprocess
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest
from utils import IntegrationTestsSplProject, create_clean_test_dir

from spl_core.project_creator.creator import Creator, main, parse_arguments
from spl_core.project_creator.variant import Variant


def execute_command(command: str) -> CompletedProcess[bytes]:
    return subprocess.run(command.split())


@pytest.mark.skip(reason="The project creator is obsolete. We use the Kickstart project instead.")
class TestProjectGenerator:
    def test_creator_materialize(self):
        "Create a new project with two variants"
        out_dir = create_clean_test_dir("test_creator_materialize")
        project_name = "MyProject"
        creator = Creator(project_name, out_dir.path)
        variants = [Variant("Variant1"), Variant("Variant2")]

        "Call IUT"
        workspace_dir = creator.materialize(variants)

        "Check results"
        assert workspace_dir == out_dir.joinpath(project_name)
        assert workspace_dir.joinpath("CMakeLists.txt").exists()
        assert workspace_dir.joinpath("variants/Variant1/config.cmake").exists()
        assert workspace_dir.joinpath("variants/Variant2/config.cmake").exists()
        cmake_variants_file = workspace_dir.joinpath(".vscode/cmake-variants.json")
        assert cmake_variants_file.exists()
        cmake_variants_text = cmake_variants_file.read_text().strip()
        "There shall not be any empty lines in resulting json file."
        assert "" not in cmake_variants_text.replace("\r\n", "\n").split("\n")
        cmake_variants_json = json.loads(cmake_variants_text)
        assert len(cmake_variants_json["variant"]["choices"]) == 2
        assert "Variant1" in cmake_variants_json["variant"]["choices"]
        assert "Variant2" in cmake_variants_json["variant"]["choices"]
        assert "Variant3" not in cmake_variants_json["variant"]["choices"]
        assert "flavor/subsystem" not in cmake_variants_json["variant"]["choices"]
        assert cmake_variants_json["variant"]["default"] == "Variant1"
        "Shall be able to find existing variants from a project"
        assert creator.collect_project_variants() == variants

    def test_creator_project_description(self):
        "Call IUT"
        project_description = Creator.create_project_description("SomeProject", [Variant("Variant1"), Variant("Variant2")])
        "Check results"
        assert project_description == {"name": "SomeProject", "touch_components": True, "touch_tools": True, "variants": {"0": {"name": "Variant1"}, "1": {"name": "Variant2"}}}

    def test_creator_parse_arguments_project(self):
        out_dir = create_clean_test_dir()
        user_arguments = ["workspace", "--name", "MyProject1", "--variant", "Variant1", "--out_dir", f"{out_dir.path}"]

        "Call IUT"
        parsed_arguments = parse_arguments(user_arguments)

        "Check results"
        assert parsed_arguments.name == "MyProject1"
        assert parsed_arguments.out_dir == out_dir.path
        assert parsed_arguments.variant == [Variant("Variant1")]

        "The variant argument can be used multiple times"
        user_arguments = ["workspace", "--name", "MyProject1", "--variant", "Variant1", "--variant", "Variant2", "--out_dir", f"{out_dir.path}"]

        "Call IUT"
        parsed_arguments = parse_arguments(user_arguments)

        "Check results"
        assert parsed_arguments.name == "MyProject1"
        assert parsed_arguments.out_dir == out_dir.path
        assert parsed_arguments.variant == [Variant("Variant1"), Variant("Variant2")]

    def test_creator_parse_arguments_variant_add(self):
        out_dir = create_clean_test_dir()
        user_arguments = ["variant", "--add", "Variant1", "--workspace_dir", f"{out_dir.path}"]

        "Call IUT"
        parsed_arguments = parse_arguments(user_arguments)

        "Check results"
        assert parsed_arguments.add == [Variant("Variant1")]
        assert parsed_arguments.delete is None
        assert parsed_arguments.workspace_dir == out_dir.path

    def test_creator_parse_arguments_variant_delete(self):
        out_dir = create_clean_test_dir()
        user_arguments = ["variant", "--delete", "Variant1", "--workspace_dir", f"{out_dir.path}"]

        "Call IUT"
        parsed_arguments = parse_arguments(user_arguments)

        "Check results"
        assert parsed_arguments.add is None
        assert parsed_arguments.delete == [Variant("Variant1")]
        assert parsed_arguments.workspace_dir == out_dir.path

    def test_creator_parse_arguments_invalid(self):
        out_dir = create_clean_test_dir()
        user_arguments = ["variant", "--name", "MyProject", "--workspace_dir", f"{out_dir.path}"]

        "Call IUT and catch SystemExit exception"
        with pytest.raises(SystemExit) as raised_exception:
            parse_arguments(user_arguments)

        "exit code is not zero for invalid arguments"
        assert raised_exception.value.code == 2

    @pytest.mark.parametrize(
        "user_arguments",
        [(["--help"]), (["workspace", "--help"]), (["variant", "--help"])],
    )
    def test_creator_parse_arguments_help(self, user_arguments):
        "Call IUT and catch SystemExit exception"
        with pytest.raises(SystemExit) as raised_exception:
            parse_arguments(user_arguments)
        "exit code is zero for valid arguments"
        assert raised_exception.value.code == 0

    def test_creator_add_variant(self):
        workspace_dir = IntegrationTestsSplProject.create_default("test_creator_add_variant")
        workspace_dir.joinpath("variants/Variant1/config.txt").write_text("")
        creator = Creator.from_folder(workspace_dir)

        "Call IUT"
        creator.add_variants([Variant("Variant3")])

        "Existing flavors shall not be overwritten"
        assert workspace_dir.joinpath("variants/Variant1/config.txt").read_text() == ""
        "New flavor files are generated"
        assert workspace_dir.joinpath("variants/Variant3/config.cmake").exists()
        cmake_variants_file = workspace_dir.joinpath(".vscode/cmake-variants.json")
        assert cmake_variants_file.exists()
        cmake_variants_json = json.loads(cmake_variants_file.read_text().strip())
        assert len(cmake_variants_json["variant"]["choices"]) == 3

    def test_creator_delete_variant(self):
        workspace_dir = IntegrationTestsSplProject.create_default("test_creator_delete_variant")
        creator = Creator.from_folder(workspace_dir)

        "Call IUT"
        creator.delete_variants([Variant("Variant2")])

        "Existing flavors shall not be overwritten"
        assert workspace_dir.joinpath("variants/Variant1/config.txt").exists()
        assert not workspace_dir.joinpath("variants/Variant2/config.txt").exists()

    def test_creator_main(self):
        out_dir = create_clean_test_dir("test_creator_main")

        "Call IUT"
        with patch("sys.argv", ["some_name", "workspace", "--name", "MyProject1", "--variant", "Variant1", "--variant", "Variant2", "--out_dir", f"{out_dir.path}"]):
            main()

        project_dir = out_dir.joinpath("MyProject1")

        "Dependency files shall exist"
        assert project_dir.joinpath("Pipfile").exists()
        assert project_dir.joinpath("scoopfile.json").exists()
        "CMake files shall exist"
        assert project_dir.joinpath("CMakeLists.txt").exists()
        "git config script shall exist"
        assert project_dir.joinpath("tools/setup/git-config.ps1").exists()
        "Variants configuration shall exist"
        assert project_dir.joinpath("variants/Variant1/config.cmake").exists()
        assert project_dir.joinpath("variants/Variant2/config.cmake").exists()

        "Add new variant and build again"
        with patch("sys.argv", ["some_name", "variant", "--add", "Variant3", "--workspace_dir", f"{project_dir}"]):
            main()

        "Variant configuration shall exist"
        assert project_dir.joinpath("variants/Variant1/config.cmake").exists()
        assert project_dir.joinpath("variants/Variant2/config.cmake").exists()
        assert project_dir.joinpath("variants/Variant3/config.cmake").exists()

        "Remove two variants and build again"
        with patch("sys.argv", ["some_name", "variant", "--delete", "Variant1", "--delete", "Variant3", "--workspace_dir", f"{project_dir}"]):
            main()

        "Variant configuration shall exist"
        assert not project_dir.joinpath("variants/Variant1/config.cmake").exists()
        assert project_dir.joinpath("variants/Variant2/config.cmake").exists()
        assert not project_dir.joinpath("variants/Variant3/config.cmake").exists()
