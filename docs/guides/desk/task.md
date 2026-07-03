# BTU Task

Defines a callable Python job.

## Required fields

- **Function** — dotted import path (`package.module.function`)
- **Queue Name** — must match a bench worker queue

## Optional fields

- **Function Arguments** — JSON kwargs
- **Max Duration** — overrides default from BTU Configuration
- Email notification settings and recipients

## Actions

- Run on demand (creates Task Log immediately)
- Link from one or more Task Schedules

## Samples

See `btu/samples/` in the app repository for example target functions.
