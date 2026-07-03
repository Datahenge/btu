# Architecture Decision Records (ADR)

Short, durable notes on **why** BTU is shaped the way it is. Each ADR captures one decision; the full narrative lives in [Technical Design](../../technical_design.md).

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-two-component-architecture.md) | Two-component architecture (Frappe app + daemon) | Accepted |
| [0002](0002-mandatory-scheduler-daemon.md) | External scheduler daemon is mandatory | Accepted |
| [0003](0003-frappe-scheduler-insufficient-for-users.md) | Frappe built-in scheduler is not a user product | Accepted |
| [0004](0004-run-later-visibility-over-rq-delay.md) | Run Later prioritizes Desk visibility over RQ delay | Accepted |
| [0005](0005-redis-rpc-control-plane.md) | Redis RPC as scheduler control plane | Accepted |

## Format

Each record includes **Context**, **Decision**, and **Consequences**. Status values: Proposed, Accepted, Deprecated, Superseded.

When a decision is reversed, add a new ADR and mark the old one Superseded — do not silently rewrite history.
