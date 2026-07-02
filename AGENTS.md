# AGENTS.md

## Project Overview

**spl-core** is a CMake module framework for Software Product Line (SPL) support. It enables
managing multiple product variants from a single repository through CMake-based build
integration, KConfig feature models for compile-time configuration, automated unit test
execution with mock generation (via Hammocking), and coverage/documentation generation per
variant.

## Architecture

> **Internal architecture docs:** see `docs/internals/`. Architecture decisions
> (ADRs, under `docs/internals/decisions/`) and requirements (under
> `docs/internals/requirements/`) live there and **must be consulted when
> analysing a task** — check for an existing decision before changing
> architecture, and record significant new decisions as an ADR.

```
src/spl_core/
├── main.py                # CLI entry point ("please" command for project init)
├── __init__.py            # Package version (__version__)
├── __run.py               # Script runner
├── common/                # Shared Python utilities (path helpers)
├── config/                # KConfig default configuration
├── kconfig/               # KConfig integration (feature model parsing via kconfiglib)
├── kickstart/             # Project template generation (cookiecutter)
│   └── templates/         # project/ and application/ scaffolds
├── gcov_maid/             # Coverage report cleanup (gcda/gcno management)
├── report_generation/     # Sphinx documentation integration
├── steps/                 # Pipeline steps (CollectPRChanges)
├── test_utils/            # Test infrastructure (SplBuild, JUnit merger, artifacts)
├── common.cmake           # Core CMake macros (spl_add_component, test suites, hammocking)
├── spl.cmake              # Main SPL CMake module (variant/build-kit setup)
├── kconfig.cmake          # KConfig CMake integration
└── conan.cmake            # Conan package manager integration
```

**Key CMake macros** (in `common.cmake`):
- `spl_add_source()` — Register production source files for a component
- `spl_add_test_source()` — Register test source files
- `spl_create_component()` — Create a component with build targets
- `_spl_add_test_suite()` — Internal: sets up test executable, hammocking mock generation,
  coverage collection, and JUnit reporting

**Key Python classes** (in `test_utils/`):
- `SplBuild` — Python wrapper around CMake/Ninja build orchestration
- `BaseVariantTestRunner` — Per-variant test execution (legacy)
- `JunitMerger` — Merges JUnit XML reports from multiple components

**Entry points** (defined in `pyproject.toml`):
- `please` → `spl_core.main:main` (project initialization CLI)
- `junit_merger` → `spl_core.test_utils.junit_merger:main`

## Tech Stack

- **Language:** Python >=3.10, <3.12
- **Package Manager:** Poetry (virtualenvs in-project: `.venv/`)
- **Build System:** CMake + Ninja (for C/C++ variants)
- **Key dependencies:** kconfiglib (feature models), hammocking (mock generation),
  gcovr (coverage), cookiecutter (templates), Sphinx (docs), pypeline-runner (build pipeline)
- **Testing:** pytest + pytest-cov
- **Linting:** ruff, mypy (strict), pre-commit hooks, codespell
- **CI/CD:** GitHub Actions → python-semantic-release → PyPI
- **System deps:** MinGW with LLVM (via Scoop on Windows)

## Build & Test

```powershell
# Full pipeline (install + tests + docs)
.\build.ps1

# Clean build (removes .venv)
.\build.ps1 -clean

# Install dependencies only
.\build.ps1 -install

# Run tests directly via pytest
poetry run pytest

# Run specific test categories
poetry run pytest -m unit
poetry run pytest -m integration
```

The build pipeline is defined in `pypeline.yaml` and executed by `pypeline-runner`:
1. Create virtual environment (Python 3.11)
2. Install Scoop packages (MinGW toolchain)
3. Run pytest
4. Generate Sphinx documentation

## Code Conventions

- **Style:** ruff with line-length 220, target Python 3.8+ syntax
- **Type checking:** mypy strict in production code (`disallow_untyped_defs`,
  `disallow_any_generics`); relaxed in `tests/` (`allow_untyped_defs`)
- **Formatting:** 4-space indentation, UTF-8, LF line endings (`.editorconfig`)
- **Imports:** isort via ruff (first-party: `spl_core`, `tests`)
- **Docstrings:** Not enforced (D100-D107 are ignored), but welcome for complex logic
- **Paths:** Use `pathlib.Path` in Python code
- **Naming:** PascalCase classes, snake_case functions/methods, UPPER_CASE CMake variables
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, etc.) — enforced
  by commitlint and commitizen pre-commit hook. Unlimited line lengths allowed.
- **Comments:** Only add comments for complex logic or non-obvious decisions. Code should
  be self-explanatory through clear naming.
- **Documentation:** Written in English. Code comments in English.

## Testing Guidelines

- Tests live in `tests/` organized by category:
  - `tests/unit/` — Unit tests (`@pytest.mark.unit`)
  - `tests/integration/` — Integration tests (`@pytest.mark.integration`)
  - `tests/cmake/` — CMake-specific tests
  - `tests/steps/` — Pipeline step tests
- Test fixtures (sample SPL projects) are in `tests/data/application/`
- Test output: `out/test-report.xml` (JUnit format)
- Use `tests/utils.py` for shared test base classes
  (`SplProjectIntegrationTestBase`, `SplKickstartProjectIntegrationTestBase`)
- Integration tests perform full CMake builds and require the MinGW toolchain
- Follow **TDD** when implementing features: write failing test → implement → verify green

## CI Pipeline

1. **Lint** (ubuntu-latest) — pre-commit hooks + commitlint
2. **Test** (windows-latest) — full `.\build.ps1` pipeline, publishes JUnit results
3. **Release** (ubuntu-latest) — python-semantic-release to PyPI + GitHub Releases
   (only on `develop` branch or manual `workflow_dispatch`)

## Branching & Release Strategy

- **`develop`** is the default/production branch (not `main`)
- All PRs target `develop`
- Merges to `develop` trigger semantic releases
- Non-develop branches produce prerelease versions (no-op for release)
- Version tracked in: `pyproject.toml`, `src/spl_core/__init__.py`, `docs/conf.py`
- Changelog excludes `chore*` and `ci*` commits

## Common Patterns

### CMake Build Flow

1. SPL project sets `VARIANT` to select a product variant
2. KConfig generates `autoconf.h` with feature flags
3. Components are added via `spl_add_source()` / `spl_create_component()`
4. Test suites use partial linking + Hammocking for automatic mock generation
5. Coverage collected per component via gcovr, merged at variant level

### Hammocking Integration (`common.cmake:751-760`)

Hammocking is invoked as a CMake custom command during the test build:
```cmake
COMMAND python -m hammocking
    --suffix _${COMPONENT_NAME}
    --sources ${PROD_SRC}
    --plink ${CMAKE_CURRENT_BINARY_DIR}/${PROD_PARTIAL_LINK}
    --outdir ${CMAKE_CURRENT_BINARY_DIR}
    <include dirs> <compile defs> <compiler includes> -x c
```
Output: `mockup_<component>.cc` and `mockup_<component>.h` for GoogleTest.

### Config File Pattern for External Tools

spl-core already uses a pattern for passing config files to external tools (e.g., Sphinx):
- Generate/locate a config file (JSON or INI)
- Pass the file path via CMake variable or environment variable
- Use `${CMAKE_COMMAND} -E env VAR=value` in `add_custom_command()`

### Variant Structure

Each variant creates separate build directories per variant/build-kit combination.
Binary naming: variant path `/` is converted to `_`
(e.g., `Variant/SubVariant` → `Variant_SubVariant`).

## Important Notes

- The main branch is **`develop`** (not `main`)
- Tests run on **Windows** (windows-latest in CI) — the CMake toolchain targets MinGW/GCC
- The `.venv/` directory is created in-project (see `poetry.toml`)
- Kickstart templates under `src/spl_core/kickstart/templates/` are cookiecutter templates —
  they contain `{{ }}` Jinja2 syntax that is NOT Python code
- The `bootstrap.json` and `.bootstrap/` directory handle initial environment setup
  (downloaded at install time, not checked into git)
- Scoop (Windows package manager) is used for system-level dependencies (`scoopfile.json`)
- Documentation is hosted on ReadTheDocs, built with Sphinx + myst-parser (Markdown support)
