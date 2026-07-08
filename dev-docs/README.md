# Internal developer docs

This folder holds **maintainer-only** documentation that is intentionally **not** part of
the published site at <https://btu.datahenge.com/>.

MkDocs builds only the `docs/` directory, so anything here stays in the repository for
contributors without appearing on GitHub Pages.

## Contents

- [`adr/`](adr/) — Architecture Decision Records (numbered design decisions)
- [`repository-layout.md`](repository-layout.md) — Python package structure

User-facing documentation lives under [`../docs/`](../docs/); start with
[`../docs/index.md`](../docs/index.md).
