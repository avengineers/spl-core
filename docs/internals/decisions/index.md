# Architecture Decision Records (ADRs)

An Architecture Decision Record captures a single significant decision: its
context, the decision itself, the alternatives considered, and the consequences.

Conventions:

* One decision per file, named `NNNN-kebab-title.md` (zero-padded, sequential).
* Numbers are never reused. Superseded ADRs are kept and marked
  `Status: superseded by NNNN`.
* Use the [template](template.md) for new records.

```{toctree}
:maxdepth: 1

template
0001-report-navigation-is-jinja-driven
0002-build-wrapper-lives-in-the-spl
```
