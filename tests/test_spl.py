from tests.utils import TestWorkspace, ExecutionTime


class TestSpl:
    def test_incremental_build(self):
        # create a new test workspace
        workspace = TestWorkspace('test_incremental_build')
        with ExecutionTime("build and run unit tests"):
            assert workspace.link().returncode == 0
        "store workspace status - all files with timestamps"
        workspace.take_files_snapshot()
        "touch a *.c file"
        workspace.get_component_file('main', 'src/main.c').touch()
        with ExecutionTime('Run CMake: link'):
            assert workspace.run_cmake(target='link').returncode == 0
        "only one object is recompiled and the binary is linked again"
        workspace_status = workspace.get_workspace_files_status()
        assert set(workspace_status.changed_files_names) == {
            '.ninja_deps', '.ninja_log', 'main.c', 'main.c.obj', 'main.exe'
        }
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0
        "reset files status before running the link again"
        workspace.take_files_snapshot()
        with ExecutionTime("Run CMake 'link' with no changes"):
            assert workspace.run_cmake(target='link').returncode == 0
        "no files are touched"
        workspace_status = workspace.get_workspace_files_status()
        assert len(workspace_status.changed_files_names) == 0
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0
        
    def test_build_with_kconfig_linking_menu(self):
        # create a new test workspace
        workspace = TestWorkspace('test_build_with_kconfig_linking_menu')
        with workspace.workspace_artifacts.kconfig_file.open("a") as file:
            file.write("""
menu "Linking"
    config LINKER_OUTPUT_FILE
        string
        default "link_out.exe"

    config LINKER_BYPRODUCTS_EXTENSIONS
        string 
        default "map,mdf"
endmenu
""")
        with ExecutionTime("build and run unit tests"):
            assert workspace.link().returncode == 0
        assert workspace.workspace_artifacts.get_build_dir(TestWorkspace.DEFAULT_VARIANT, "prod").joinpath("link_out.exe").exists()
            
