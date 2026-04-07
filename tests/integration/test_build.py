import subprocess

import pytest

from tests.utils import SplKickstartProjectIntegrationTestBase, SplProjectIntegrationTestBase


@pytest.mark.integration
class TestBuild(SplKickstartProjectIntegrationTestBase):
    def test_build_prod(self):
        files_always_touched_by_build = {
            # These files are touched because the build script explicitly calls CMake configure before build
            "TargetDirectories.txt",
            "build.ninja",
            "rules.ninja",
            "cmake.check_cache",
            "compile_commands.json",
            "build.json",
            # This file is touched every time Ninja is run
            ".ninja_log",
            # Pypeline generated setup files
            "env_setup.ps1",
            "env_setup.bat",
        }
        variant = "EnglishVariant"

        "Call IUT"
        result = self.spl_project.build(variant, "link")
        assert result is not None and result.returncode == 0, "Execution shall not fail."

        build_dir = self.spl_project.artifacts.get_build_dir(variant, "prod")
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
        self.spl_project.artifacts.src_dir.joinpath("main/src/main.c").touch()
        "store workspace status - all files with timestamps"
        self.spl_project.take_files_snapshot()

        "Call IUT"
        result = self.spl_project.build(variant, "link")
        assert result is not None and result.returncode == 0, "Execution shall not fail."

        "only one object is recompiled and the binary is linked again"
        workspace_status = self.spl_project.get_workspace_files_status()
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
        self.spl_project.take_files_snapshot()

        "Call IUT"
        result = self.spl_project.build(variant, "link")
        assert result is not None and result.returncode == 0, "Execution shall not fail."

        "No files were touched, so nothing was compiled again"
        workspace_status = self.spl_project.get_workspace_files_status()
        assert set(workspace_status.changed_files_names) == files_always_touched_by_build
        assert len(workspace_status.deleted_files) == 0
        assert len(workspace_status.new_files) == 0


@pytest.mark.integration
class TestHammocking(SplProjectIntegrationTestBase):
    def _cmake_configure(self, variant: str, extra_cmake_args: list[str]) -> subprocess.CompletedProcess[str]:
        import shutil

        cmake_exe = shutil.which("cmake")
        if cmake_exe is None:
            raise RuntimeError("cmake executable not found in PATH")

        build_dir = self.spl_project.artifacts.get_build_dir(variant, "test")
        return subprocess.run(
            [
                cmake_exe,
                "-B",
                str(build_dir),
                "-G",
                "Ninja",
                f"-DVARIANT={variant}",
                "-DBUILD_KIT=test",
                "-DBUILD_TYPE=Debug",
                "-DCMAKE_TOOLCHAIN_FILE=tools/toolchains/gcc/toolchain.cmake",
                *extra_cmake_args,
            ],
            cwd=str(self.spl_project.project_dir),
            env=self.spl_project.env,
            capture_output=True,
            text=True,
        )

    def test_hammocking_passes_project_root_dir(self):
        variant = "Variant1"

        result = self.spl_project.build(variant, "unittests")
        assert result is not None and result.returncode == 0, "Unit tests build shall not fail."

        build_ninja = self.spl_project.artifacts.get_build_dir(variant, "test").joinpath("build.ninja")
        assert build_ninja.exists(), "build.ninja must exist after configure"

        content = build_ninja.read_text(encoding="utf-8")
        assert "--project-root-dir" in content, (
            "Hammocking must be called with --project-root-dir so that ignore_symbols_outside_project (default true in hammocking >=0.11) can correctly filter out symbols from outside the SPL project root."
        )

    def test_hammocking_passes_config_file_when_set(self):
        variant = "Variant1"
        hammocking_ini = self.spl_project.project_dir / "hammocking.ini"

        result = self._cmake_configure(variant, [f"-DHAMMOCKING_CONFIG_FILE={hammocking_ini.as_posix()}"])
        assert result.returncode == 0, f"CMake configure failed:\n{result.stderr}"

        build_ninja = self.spl_project.artifacts.get_build_dir(variant, "test").joinpath("build.ninja")
        assert build_ninja.exists(), "build.ninja must exist after configure"

        content = build_ninja.read_text(encoding="utf-8")
        assert "--config" in content, "Hammocking must be called with --config when HAMMOCKING_CONFIG_FILE is set."
