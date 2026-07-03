# Developer documentation

Notes for contributors and maintainers (not published for end users unless linked from the main index).

| Document | Description |
|----------|-------------|
| [Technical design](../technical_design.md) | Why BTU is two components; Run Later; mental model |
| [Architecture Decision Records](adr/README.md) | Numbered ADRs (posterity / rationale) |
| [Repository layout](repository_layout.md) | How the BTU Python package is organized |
| [Scheduler Redis RPC](../scheduler_redis_rpc.md) | Protocol between Frappe and the BTU Scheduler daemon |
| [Archived scripts (Gists)](gists.md) | Generic bench/server utilities removed from the app |

In-app README files:

- `btu/samples/README.md` — functions to point BTU Tasks at
- `btu/diagnostics/README.md` — `bench execute` smoke tests
