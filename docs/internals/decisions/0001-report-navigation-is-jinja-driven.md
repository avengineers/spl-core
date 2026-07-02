# 0001 — Report navigation is Jinja/data-driven

- Status: accepted
- Date: 2026-07-01
- Deciders: SPL Core maintainers, architecture review

## Context

While unifying the report look-and-feel on the PyData Sphinx Theme, a Python
page generator was added to the Sphinx theme extension
(`spl_theme_extension._generate_component_pages`) to emit per-component
`{component}_index.md` wrapper pages for the report sidebar. During review it
turned out this duplicated an already existing mechanism: the report navigation
is built entirely from `build_config` (written by `common.cmake` as
`config.json`) and the project's Jinja templates (`index.md`,
`doc/components/index.md`), rendered via `rstjinja` on Sphinx `source-read`.
See {doc}`../architecture/report_generation`.

## Decision

Report navigation is data-driven via the project Jinja templates only. Pages are
**not** generated from a Sphinx extension. The per-component sub-pages are
collected inline in `doc/components/index.md` by iterating
`build_config.components_info` (flat list, grouped by headings).

## Alternatives considered

- Option A (chosen) — Flat list like the pre-existing templates; remove the
  wrapper pages and the extension-side page generation entirely.
- Option B — One collapsible sidebar node per component via pure Jinja. Rejected:
  Sphinx cannot emit N files from a single Jinja source, so it still needs N
  generated files.
- Option C — Generate the wrapper pages in `common.cmake` via `file(WRITE ...)`.
  Rejected for now: adds files/scaffolding for a purely cosmetic sidebar grouping.

## Consequences

- Positive: single source of truth for navigation; no duplicated collection
  logic in Python; simpler theme extension (CSS/logo/needs-dark only).
- Negative / trade-offs: components are listed flat under one "Components" page
  (grouped by headings), without a dedicated collapsible node per component.
- Follow-ups: if a per-component sidebar node is wanted later, reconsider Option
  C as a separate, explicit decision.
