from pathlib import Path
from typing import List

from spl_core.test_utils.base_variant_test_runner import BaseVariantTestRunner


class Test_EnglishVariant(BaseVariantTestRunner):
    @property
    def component_paths(self) -> List[Path]:
        return [
            Path("src/greeter"),
        ]

    @property
    def expected_build_artifacts(self) -> List[Path]:
        return [Path("my_main.exe"), Path("compile_commands.json")]
