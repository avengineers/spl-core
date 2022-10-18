from tests.utils import TestUtils, TestWorkspace, ExecutionTime


class TestSpl:
    def test_incremental_build(self):
        workspace = TestWorkspace("test_incremental_build")
        with ExecutionTime("build and run unit tests"):
            assert workspace.link().returncode == 0
        "store workspace status - all files with timestamps"
        workspace.take_files_snapshot()
        "touch a *.c file"
        workspace.get_component_file("main", "src/main.c").touch()
        with ExecutionTime("Run CMake: link"):
            assert workspace.run_cmake(target="link").returncode == 0
        "only one object is recompiled and the binary is linked again"
        workspace_status = workspace.get_workspace_files_status()
        assert set(workspace_status.changed_files_names) == {
            ".ninja_deps",
            ".ninja_log",
            "main.c",
            "main.c.obj",
            "main.exe",
        }
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0
        "reset files status before running the link again"
        workspace.take_files_snapshot()
        with ExecutionTime("Run CMake 'link' with no changes"):
            assert workspace.run_cmake(target="link").returncode == 0
        "no files are touched"
        workspace_status = workspace.get_workspace_files_status()
        assert len(workspace_status.changed_files_names) == 0
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

    def test_support_external_components(self):
        workspace = TestWorkspace("test_support_external_components")
        external_component_path = TestUtils.create_clean_test_dir("external_component").path
        workspace.add_external_component(external_component_path)
        with ExecutionTime("link"):
            assert workspace.link().returncode == 0
        "External components are referred by the hash of their absolute path"
        assert workspace.get_component_obj_file('external_component').exists()
