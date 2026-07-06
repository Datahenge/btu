# IANA Timezone Cache

This document explains how BTU populates and validates the **Cron Time Zone** field on BTU Task Schedules, and why the design avoids hardcoding timezone data anywhere in the codebase.

---

## The Problem

A cron schedule must know what timezone to interpret its time fields in. Frappe stores a site-wide timezone (in System Settings), but individual BTU Task Schedules may need to run in a different timezone — for example, a schedule that must fire at midnight New York time on a server located in London.

The field needs to:

1. Prevent typos — `America/New_York` is valid; `America/NewYork` is not.
2. Stay current — the IANA timezone database is updated several times per year as governments change DST rules.
3. Not hardcode anything — a static list in the DocType JSON or Python source becomes stale the moment it is written.

---

## The Solution: zoneinfo + Redis Cache

The authoritative source for valid timezone names is the **OS zoneinfo database**, accessed via Python's standard-library `zoneinfo` module:

```python
from zoneinfo import available_timezones
sorted(available_timezones())  # → ['Africa/Abidjan', 'Africa/Accra', ...]
```

This list reflects whatever timezone data is installed on the server (`tzdata` package on Debian/Ubuntu). When the OS package is updated, the list is automatically up to date — no BTU code change required.

Because building this list on every form load or every `validate()` call would be wasteful, BTU caches it in **Frappe's Redis cache**.

---

## How It Works

### Python (`btu/btu_core/form_options.py`)

```
_build_timezone_list()        — calls zoneinfo, returns sorted list
_get_cached_timezones()       — checks Redis; calls _build_timezone_list() on miss
get_cron_timezones()          — @whitelist; returns _get_cached_timezones()
reload_timezone_cache()       — @whitelist; forces rebuild and stores in Redis
validate_cron_timezone(name)  — checks name against set(_get_cached_timezones())
```

**Cache key:** `btu_iana_timezones`  
**Cache backend:** Frappe's Redis cache (`frappe.cache`)  
**TTL:** None — the entry persists until Redis is flushed or `reload_timezone_cache()` is called.

The cache is **lazy**: it is populated on the first call after Redis starts (or after a flush), not at application startup. A cold-cache miss adds roughly 5–10 ms to that single request; all subsequent calls are Redis reads.

`validate_cron_timezone()` uses the same cache path, so if the cache is cold during a `validate()` call (e.g., inside a bench script), it rebuilds automatically rather than incorrectly rejecting a valid timezone.

### JavaScript (`btu_task_schedule.js`)

On form `onload`, the JS calls `btu.btu_core.form_options.get_cron_timezones` once and passes the result to `ctrl.set_data()` on the `cron_timezone` Autocomplete control. This feeds the list directly into the underlying Awesomplete widget, which provides **contains-match filtering** as the user types.

The result is stored on `frappe._btu_timezones` for the lifetime of the browser session, so navigating between multiple BTU Task Schedule records makes only one server round-trip total.

### BTU Configuration button

**BTU Configuration → Maintenance / Repairs → Reload Timezone Cache**

This button calls `reload_timezone_cache()`, which rebuilds the list from `zoneinfo` and writes it back to Redis. Use it when:

- The server's `tzdata` package was updated and you want the new zones available immediately, without waiting for a Redis flush or server restart.
- Redis was flushed manually and you want to pre-warm the cache before users open the form.

---

## What Is Not Hardcoded

| Thing | Where it comes from |
|---|---|
| List of valid timezones | OS `tzdata` via Python `zoneinfo` |
| Cache key TTL | Permanent (Redis default, no expiry set) |
| Validation logic | Derives from the same cached list |
| Form dropdown options | Fetched at runtime from Redis via `frappe.call` |

There is no static list of timezone strings anywhere in BTU source code or DocType JSON.

---

## Updating Timezone Data on the Server

BTU itself requires no changes when IANA releases a new timezone database. The update path is:

```bash
sudo apt update && sudo apt install --only-upgrade tzdata
# Then, in BTU Configuration:
#   click "Reload Timezone Cache"
# Or wait — the cache self-populates on next Redis flush / server restart.
```
