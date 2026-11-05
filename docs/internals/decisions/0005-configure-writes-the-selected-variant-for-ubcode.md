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
file**, a JSON file named by `[variants] data_file` (the Sphinx option
`needs_variant_data_file`), whose values the `{if}` directive
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
that run's `config.json`. It does so always, with or without `SPL_UBCODE_SELECTION_FILE`.
This is the one file Sphinx and ubCode share: Sphinx reads it as `needs_variant_data_file`,
ubCode as `[variants] data_file`, and a document reads its values as `var.*` in an `{if}`
condition.

```json
{
  "features": {"AUTO_OFF": true, "BLINKING": false, "CUSTOMER": "B"},
  "build_config": {"variant": "Sleep", "target": "reports"}
}
```

| Field | What it holds | Who reads it |
| --- | --- | --- |
| `features` | Every KConfig symbol with the variant's value. Every boolean the feature model declares is present, also the promptless ones KConfig leaves out when they are off, so a condition on any of them has an answer. `{}` for an SPL without a KConfig model. | Documents: `{if} var.features.BLINKING` |
| `build_config.variant` | The variant's name, as under `variants/`. | Documents: `{if} var.build_config.variant == "Sleep"`, such as a title page per variant |
| `build_config.target` | The run's target, `docs` or `reports`. ubCode always gets the file of the `reports` run, so it shows the report content. | Documents: `{if} var.build_config.target == "reports"`, content that only a report shows |

The file holds only fields a document reads. A field joins when a document needs it.

#### How configure writes it

- `kconfig.py --out_features_file`, called next to the existing outputs, writes
  `<build>/kconfig/features.json`. `KConfig.declared_boolean_symbols()` adds the
  promptless booleans. `autoconf.h`, `autoconf.json` and `autoconf.cmake` stay as they are.
- `_spl_write_variant_data()` in `common.cmake` adds `build_config` to that document and
  writes it next to each run's `config.json`.

#### What changes in the Sphinx runs

Only with `SPL_UBCODE_SELECTION_FILE`; without it, configure adds nothing to the Sphinx
commands or the `config.json` files.

- Every Sphinx run spl-core starts gets its own variant data file through
  `-D needs_variant_data_file=<file>`, so runs of different builds stay independent.
- A component's own runs get a root page that spl-core generates: `root_docs.md` and
  `root_reports.md` in the component's binary directory. The run gets it with
  `-D root_doc` and in its `include_patterns`, and it includes only that component's
  documents. The pages lie outside the run output directories, so the variant runs never
  read them. The SPL's `index.md` then needs no switch between a variant report and a
  component report. For components that have a docs run, configure removes root pages of
  an earlier configure when the variable is not set.
- The variant's report wrapper pages and the component root pages come from one toctree
  source, `_spl_component_page_content()`. A component's reports-run `variant_data.json`
  exists only when the component has reports.

### The ubCode selection

When the SPL sets `SPL_UBCODE_SELECTION_FILE` (a path relative to the project root, for
example `ubproject.variants.toml`), configure writes that file. The SPL's committed
`ubproject.toml` names it with `extend`, and the SPL keeps it out of git. It holds:

- `[variants] data_file`: the variant-level `reports` file of this build, as a path
  relative to the project root. See "Which key names the file" below.
- `[parse.parsers.md]` with `flavour = "myst"` and `[parse.parsers.rst]`, each with an
  `include` list: the documents of this build. These are the same patterns
  the variant `reports` run's `config.json` gives Sphinx, plus this build's generated pages (test
  specifications, test results, coverage, source listings), read where the build writes
  them. ubCode 0.37 and later evaluates the `test-report` directive of the results pages
  itself, so the test cases and the `results` links reach ubCode without a converter.
  A pattern without a slash, such as `index.md`, is written as `./index.md`: ubCode matches
  a bare file name in every directory, so `index.md` would select every component's
  `doc/index.md`.
  The md parser also gets the MyST extensions Sphinx gets, so that ubCode reads the
  `:::{if}` blocks of the colon fence; `html_admonition` is left out, because ubCode does
  not implement it.
- spl-core's `report_generation/ubproject.toml`, copied from the installed spl-core at
  configure: its `[source]` table (`respect_gitignore = false`), which lets ubCode read the
  gitignored `build/` dir; an empty `[test_reports]` table, without which ubCode
  does not know the `test-report` directive; and spl-core's needs model, the need types, link types
  and fields. The copy cannot drift, and no path into the virtualenv is involved. The SPL's committed
  `ubproject.toml` declares no needs model of its own, because `extend` replaces arrays
  such as `[[needs.types]]`. Sphinx keeps reading spl-core's file through
  `needs_from_toml`.

#### Why ubCode gets a file of its own

Sphinx and ubCode already share the variant data file. The selection adds only what
ubCode's configuration format needs, which Sphinx gets elsewhere:

- The document set. Sphinx gets it as `include_patterns` in each run's `config.json`;
  ubCode gets it as the parsers' `include` lists.
- The needs model and `[test_reports]`. Sphinx reads spl-core's `ubproject.toml` through
  `needs_from_toml`.

The two tools also need the information in different places. Sphinx needs one
configuration per run, and a build starts several runs. ubCode needs one file at a fixed
path, which the committed `ubproject.toml` names with `extend`. And `config.json` is the
Jinja context `build_config` of every SPL's `conf.py` and templates, so a change to its
format reaches every SPL. A single file for both tools is possible; see "Alternatives
considered".

The patterns are split between the two parsers, so that the md parser does not claim
`.rst` pages:

- A pattern that ends in `/**` goes to the md parser as `/**/*.md` and to the rst parser
  as `/**/*.rst`.
- Any other pattern goes to the parser its suffix names (`.md` or `.rst`).
- A pattern with neither form reaches no parser. Configure prints a WARNING that names
  it, so a pattern is not dropped without a word.

Only a test-kit configure writes the selection, because only the test kit has
documentation runs. The prod kit builds the target binaries, and a prod configure leaves
the selection as it was. The last test-kit configure wins. Selecting a variant in CMake
Tools configures it, so ubCode follows the selection. Without the variable, configure
writes nothing into the source tree, and an SPL that does not use ubCode sees no change
in its Sphinx commands.

#### Which key names the file

The selection uses `[variants] data_file`. In sphinx-needs 9.1 and in ubCode this is the
current key; `[needs] variant_data_file` is their legacy location (checked in
`needs.py`, `_load_variants_from_toml`, and in the ubCode schema). Both tools read one
location whole: as soon as `[variants]` sets `data` or `data_file`, they ignore the
legacy `[needs]` variant keys. So the selection wins over any `[needs] variant_data*` key
that an SPL's committed `ubproject.toml` still sets. Sphinx itself never reads the
selection file; it gets the file through `-D needs_variant_data_file`.

The document set has one source: CMake's include patterns. Sphinx and ubCode read the same
list, so a component the variant leaves out is missing from both. An SPL's own documents
outside its components (`index.md`, `doc/**`) reach both through
`SPL_PROJECT_DOCS_INCLUDE_PATTERNS` (default empty), which spl-core prepends to the
variant `docs` and `reports` include patterns, so that `conf.py` and the committed
`ubproject.toml` declare no include list of their own.
`extend` replaces arrays rather than merging them, so a list declared in two places would
silently hide one of them.

### What ubCode does with Jinja

ubCode and `ubc` render no Jinja. A document that still uses Jinja does not break them:
they report no error and no extra warning. They read the document as if every Jinja
condition were true. Content inside `{% if %}` shows in every variant, needs included, and
`{{ … }}` shows as text. Checked with `ubc` 0.39 on SPLED: a need inside
`{% if config.NOT_SET %}` was indexed, and `{{ config.BLINKING }}` stayed text.

An SPL can therefore convert step by step:

- Content that ubCode must show per variant goes into `{if}` blocks: needs, and text
  that depends on a feature or on the target, such as `{if} var.features.BLINKING` or
  `{if} var.build_config.target == "reports"`.
- Navigation uses toctree globs. The include set narrows a glob to the documents of the
  build, so `doc/components/index.md` lists the variant's components with no loop.
- Other content can keep its Jinja for now. ubCode shows it unrendered.
- While the SPL's `conf.py` renders Jinja, `SPL_SOURCE_DOCS_JINJA_RAW_TAGS` stays `ON`,
  and ubCode shows the `{% raw %}` lines on the source listing pages as text. Once no
  document needs Jinja, the SPL removes the Jinja hook and sets the option to `OFF`.

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
- **One configuration file for Sphinx and ubCode.** Each run's `config.json` becomes a
  TOML file in ubCode's format that `conf.py` reads, and the root selection only
  `extend`s the selected run's file. ubCode follows an `extend` chain and accepts tables
  it does not know, so this works. Not chosen now: it changes the `conf.py` contract and
  the Jinja context of every SPL, a breaking change. It can follow as a change of its own.
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
  - Content left in Jinja shows in every variant in ubCode.
  - `{if}` switches whole blocks, not single lines. Content that Jinja switched inside one
    element, such as a line in a Mermaid diagram, becomes two blocks.
- Follow-ups:
  - An SPL that needs need types of its own has no place for them yet. It gets one when
    the first SPL needs it.
  - The SPLED integration (`avengineers/SPLed`): its `ubproject.toml`, the conversion of
    its documents, and a check that ubCode and Sphinx agree.
  - Running `ubc` in CI needs `useblocks/ubc-action` and a license key as a repository
    secret.
