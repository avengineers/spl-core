# 0001 — Report navigation is data-driven with generated per-component pages

- Status: accepted (amended 2026-07-13, reverses the earlier Option A decision)
- Date: 2026-07-01
- Deciders: SPL Core maintainers, architecture review

## Context

While unifying the report look-and-feel on the PyData Sphinx Theme, we need the
variant report's left sidebar to show one collapsible node per component, with
that component's doc and report pages nested underneath.

The report navigation is data-driven: it is built from `build_config` (written
by `common.cmake` as `config.json`) and the project's Jinja templates
(`index.md`, `doc/components/index.md`), rendered via `rstjinja` on Sphinx
`source-read`. See {doc}`../architecture/report_generation`.

The catch is theme-specific. The old `sphinx_rtd_theme` rendered Markdown
section headings (`##`) as expandable sidebar nodes, so a single
`doc/components/index.md` that emitted one heading per component produced a
per-component sidebar hierarchy for free. The PyData Sphinx Theme does **not**
do this: its left sidebar only lists actual documents (toctree targets);
headings are relegated to the right-hand "On this page" TOC. Under PyData the
heading-based approach therefore collapses into a single flat "Components" node.

Sphinx cannot emit N documents from one Jinja source, so restoring a
per-component node requires N real documents — one wrapper page per component.

## Decision

Report navigation is data-driven, **and** for the variant `reports` target
`common.cmake` generates one `{component}_index.md` wrapper page per component
with documentation (a level-1 heading plus a `toctree` to the component's doc
and report pages). `doc/components/index.md` links to those wrapper pages for
the `reports` target, so each component becomes its own collapsible sidebar
node; for the `docs` target it links directly to each component's `doc/index`.

The wrapper pages are written into the build output directory and registered via
`CMAKE_CONFIGURE_DEPENDS`, so they are regenerated on reconfigure and always
match the variant's active component set. No wrapper is written for a component
without documentation.

## Alternatives considered

- Option A — Flat list built purely from the project templates; no wrapper
  pages. Chosen originally on the assumption the per-component files were
  redundant. **Reversed**: under PyData it yields a flat sidebar with no
  per-component node, which fails the requirement.
- Option B — One collapsible sidebar node per component via pure Jinja.
  Rejected: Sphinx cannot emit N files from a single Jinja source, so it still
  needs N generated files.
- Option C (chosen) — Generate the wrapper pages in `common.cmake` via
  `file(WRITE ...)` at configure time. This keeps a single templating owner
  (CMake writes both `config.json` and the wrapper files) and needs no Sphinx
  extension or separate script.

## Consequences

- Positive: the report sidebar shows a hierarchical, per-component structure
  under PyData; generation stays in `common.cmake` next to the rest of the
  report scaffolding; the theme extension stays limited to CSS/logo/needs-dark.
- Negative / trade-offs: `common.cmake` writes extra files per component; the
  wrapper template and `doc/components/index.md` must stay in sync on the page
  set that a component report contains.
- Note: an earlier alternative generated the wrapper pages from the Sphinx theme
  extension (`spl_theme_extension._generate_component_pages`). That was removed
  in favour of generating them in `common.cmake`, keeping page collection out of
  the theme extension.
