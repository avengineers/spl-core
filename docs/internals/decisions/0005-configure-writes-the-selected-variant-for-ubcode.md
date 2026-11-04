# 0005 — CMake configure writes the selected variant for ubCode

- Status: proposed
- Date: 2026-11-04
- Deciders: SPL Core maintainers, Product Owner

## Context

ubCode (the useblocks VS Code extension) and its command-line tool `ubc` read an SPL's
documentation without running Sphinx. They read `ubproject.toml` at the project root and
the documents. They never run `conf.py`, render no Jinja, and know nothing about CMake or
KConfig.

Today an SPL's documentation depends on the variant in two ways, and ubCode can see
neither of them:

- **Which documents exist.** For every Sphinx run, `common.cmake` writes a `config.json`
  whose `include_patterns` list only the components of the variant. `conf.py` reads it
  through `SPHINX_BUILD_CONFIGURATION_FILE`. ubCode never sees it, so it reads the
  documents of every component, including the ones the variant leaves out.
- **What a document contains.** Documents switch content with Jinja
  (`{% if config.BLINKING %}`), rendered on Sphinx `source-read`, from `autoconf.json`
  (`AUTOCONF_JSON_FILE`). ubCode shows the Jinja as text.

The developer selects the variant and the build kit in the status bar of CMake Tools,
which configures the build. The C/C++ extension follows that selection. ubCode has to
follow it too, or the editor shows one variant and the documentation another.

sphinx-needs 9 and ubCode share one mechanism for the second point: a **variant data
file**, a JSON file named by `needs.variant_data_file`, whose values the `{if}` directive
reads as `var.*`. ubCode reads further configuration through `extend` in `ubproject.toml`.

useblocks built a working version in their fork of SPLED (`useblocks/SPLed`, see its
`AGENTS.md` and `VARIANTS.md`). It does everything in a standalone Python script of the
SPL, which parses `parts.cmake` a second time, so that the documentation works without a
configured build. That needs a second reader of the product structure in every SPL.

## Decision

**The CMake configure step writes everything ubCode needs to show the configured build:
a variant data file for every Sphinx run, and one generated ubCode configuration file at
the project root that selects the configured build. A configured CMake build is the
prerequisite. No SPL writes a script of its own for it.**

### The variant data file

For every Sphinx run spl-core already starts — the variant's `docs` and `reports`, and
each component's `docs` and `reports` — configure writes a `variant_data.json` next to
that run's `config.json`:

```json
{
  "features": {"AUTO_OFF": true, "BLINKING": false, "CUSTOMER": "B"},
  "build_config": {
    "variant": "Sleep",
    "kit": "test",
    "target": "reports",
    "scope": "variant",
    "component": "",
    "components": ["components/auto_off", "components/light_controller"]
  }
}
```

- `features` holds every KConfig symbol with the variant's value. Every boolean the
  feature model declares is present, also the promptless ones KConfig leaves out when they
  are off (`KConfig.declared_boolean_symbols()`), so a condition on any of them has an
  answer.
- `build_config.components` is the variant's component list as CMake knows it after
  `parts.cmake`. `scope` is `variant`, or `component` with `component` naming the
  component's path.
- Every Sphinx run spl-core starts gets its own file through
  `-D needs_variant_data_file=<file>`, so runs of different builds stay independent.
- A component's own runs get a root page that spl-core generates, passed with
  `-D root_doc`, and include only that component's documents. The SPL's `index.md` then
  needs no switch between a variant report and a component report.

### The ubCode selection

When the SPL sets `SPL_UBCODE_SELECTION_FILE` (a path relative to the project root, for
example `ubproject.variants.toml`), configure writes that file. The SPL's committed
`ubproject.toml` names it with `extend`, and the SPL keeps it out of git. It holds:

- `[needs] variant_data_file`: the variant-level `reports` file of this build.
- `[parse.parsers.*] include`: the documents of this build. These are the same patterns
  the run's `config.json` gives Sphinx, plus this build's generated pages (test
  specifications, test results, coverage, source listings), read where the build writes
  them. ubCode 0.37 and later evaluates the `test-report` directive of the results pages
  itself, so the test cases and the `results` links reach ubCode without a converter.
- spl-core's needs model: the need types, link types and fields of
  `report_generation/ubproject.toml`, copied from the installed spl-core at configure.
  The copy cannot drift, and no path into the virtualenv is involved. The SPL's committed
  `ubproject.toml` declares no needs model of its own, because `extend` replaces arrays
  such as `[[needs.types]]`. Sphinx keeps reading spl-core's file through
  `needs_from_toml`.

Only a test-kit configure writes the selection, because only the test kit has
documentation runs. The prod kit builds the target binaries, and a prod configure leaves
the selection as it was. The last test-kit configure wins. Selecting a variant in CMake
Tools configures it, so ubCode follows the selection. Without the variable, configure writes nothing into the source
tree, and an SPL that does not use ubCode sees no change.

The document set has one source: CMake's include patterns. Sphinx and ubCode read the same
list, so a component the variant leaves out is missing from both. An SPL's own documents
outside its components (`index.md`, `doc/**`) reach both through one CMake variable, so
that `conf.py` and the committed `ubproject.toml` declare no include list of their own.
`extend` replaces arrays rather than merging them, so a list declared in two places would
silently hide one of them.

### Documents without Jinja

An SPL that uses ubCode writes its documents without Jinja:

- Content that depends on a feature or on the target goes into `{if}` blocks:
  `{if} var.features.BLINKING`, `{if} var.build_config.target == "reports"`.
- Navigation uses toctree globs. The include set narrows a glob to the documents of the
  build, so `doc/components/index.md` lists the variant's components with no loop.
- The SPL sets `SPL_SOURCE_DOCS_JINJA_RAW_TAGS` to `OFF`.

This amends ADR 0001 for such an SPL. Navigation stays data-driven, and CMake still writes
the per-component wrapper pages. The data now reaches the documents through the include
set and the variant data, not through Jinja. An SPL that keeps Jinja keeps working as
before.

## Alternatives considered

- **A standalone script in each SPL (the useblocks fork).** It works without a compiler.
  Rejected: every SPL writes and maintains a second reader of `parts.cmake`, and the
  product structure is stated twice. A configured build is already the prerequisite for
  the C/C++ extension.
- **Generated conditional rules (`[[source.variant_sources]]`, read by sphinx-mounts).**
  Used by the fork. Not needed here: spl-core already computes the document set per run,
  and the same list serves ubCode. This avoids a second mechanism and the sphinx-mounts
  dependency.
- **Committed rules in `ubproject.toml`, one per component, checked by a test.** Rejected
  by the Product Owner: the component rules must be generated.
- **Extending spl-core's `ubproject.toml` inside the virtualenv.** The path contains the
  Python version, and ubCode drops an `extend` it cannot resolve without a word. The fork
  ran into this.

## Consequences

- Positive: ubCode, `ubc` and Sphinx show the same documents and the same content for the
  configured build. The selection follows CMake Tools. An SPL adds one variable, one
  `extend` line and a `.gitignore` entry, and converts its documents.
- Negative / trade-offs:
  - Without a configured test-kit build, ubCode shows no variant.
  - Several configured builds share one selection, and the last configure wins.
  - VS Code may need a window reload before ubCode shows a new selection; useblocks
    reported this.
  - `{if}` switches whole blocks, not single lines. Content that Jinja switched inside one
    element, such as a line in a Mermaid diagram, becomes two blocks.
- Follow-ups:
  - An SPL that needs need types of its own has no place for them yet. It gets one when
    the first SPL needs it.
  - The SPLED integration (`avengineers/SPLed`): its `ubproject.toml`, the conversion of
    its documents, and a check that ubCode and Sphinx agree.
  - Running `ubc` in CI needs `useblocks/ubc-action` and a license key as a repository
    secret.
