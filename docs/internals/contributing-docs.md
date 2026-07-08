# Contributing to docs

Documentation is published at [https://btu.datahenge.com/](https://btu.datahenge.com/) from this repository.

## Local build

```bash
pip install -e ".[docs]"
mkdocs serve   # http://127.0.0.1:8000
mkdocs build   # outputs site/
```

## Source layout

User docs: `docs/get-started/`, `concepts/`, `guides/`, `recipes/`, `scheduler/`, `reference/`, `integrations/`, `troubleshooting/`.

Maintainer docs: `docs/internals/` (technical design). Internal-only material that is **not** published (ADRs, repository layout) lives in `dev-docs/` at the repo root, outside the MkDocs build.

Nav is defined in [`mkdocs.yml`](https://github.com/Datahenge/btu/blob/version-16/mkdocs.yml) at repo root.

## Scheduler doc changes

User-facing scheduler content lives **here**, not on a separate scheduler docs site. When changing `btu_scheduler_py` behaviour or config, update matching pages in `docs/scheduler/`.

## PR checklist

- [ ] `mkdocs build` succeeds
- [ ] New pages added to `nav` in `mkdocs.yml` if needed
- [ ] Links use relative paths within docs
- [ ] Screenshots go in `docs/assets/images/`

## Recipe template

1. **Goal** — one sentence
2. **Prerequisites**
3. **Steps** — numbered
4. **Verify**
5. **Related links**
