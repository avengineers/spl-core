import subprocess

from tests.utils import DirectoryTracker, SplKickstartProjectIntegrationTestBase


class TestBuild(SplKickstartProjectIntegrationTestBase):
    def test_build_prod(self):
        files_always_touched_by_build = {
            # These files are touched because the build script explicitly calls CMake configure before build
            "TargetDirectories.txt",
            "build.ninja",
            "rules.ninja",
            "cmake.check_cache",
            "compile_commands.json",
            # This file is touched every time Ninja is run
            ".ninja_log",
        }
        variant = "EnglishVariant"
        result = self.cli.execute(["build.bat", "-build", "-buildKit", "prod", "-variants", variant])
        assert result.returncode == 0, "Execution shall not fail."

        build_dir = self.project_dir.joinpath(f"build/{variant}/prod")

        "Expected configuration output"
        assert build_dir.joinpath("kconfig/autoconf.h").exists()
        assert build_dir.joinpath("build.ninja").exists()

        "Expected build results for kit prod shall exist"
        executable = build_dir.joinpath("my_main.exe")
        assert executable.exists()
        my_main_result = subprocess.run([executable], capture_output=True)
        assert 0 == my_main_result.returncode
        assert "Hello, world!" == my_main_result.stdout.decode("utf-8").strip()

        "touch a *.c file to simulate a single file change"
        self.project_dir.joinpath("src/main/src/main.c").touch()
        "store workspace status - all files with timestamps"
        directory_tracker = DirectoryTracker(self.project_dir)

        "Call IUT"
        result = self.cli.execute(["build.bat", "-build", "-buildKit", "prod", "-variants", variant, "-target", "link"])
        assert result.returncode == 0, "Execution shall not fail."

        "only one object is recompiled and the binary is linked again"
        workspace_status = directory_tracker.get_status()
        assert set(workspace_status.changed_files_names) == files_always_touched_by_build | {
            # This file is touched when dependencies have changed
            ".ninja_deps",
            # Only this file was recompiled
            "main.c.obj",
            "my_main.exe",
        }
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0

        "reset files status before running the link again"
        directory_tracker.reset_status()

        "Call IUT"
        result = self.cli.execute(["build.bat", "-build", "-buildKit", "prod", "-variants", variant, "-target", "link"])
        assert result.returncode == 0, "Execution shall not fail."

        "No files were touched, so nothing was compiled again"
        workspace_status = directory_tracker.get_status()

        assert set(workspace_status.changed_files_names) == files_always_touched_by_build
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0
