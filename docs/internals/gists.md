# Archived utility scripts

Generic bench and server maintenance scripts were removed from the BTU app to keep the repository focused on scheduling. Copies are kept in GitHub Gists for personal reuse.

Add links here when you publish a gist:

| Script (former location) | Gist | Notes |
|--------------------------|------|-------|
| `btu/monitor.py` | *(add URL)* | systemd service checks, SQL process list |
| `perform_full_db_sync` (was in `examples.py`) | *(add URL)* | Force full DocType sync for all apps |
| `test_get_list` (was in `examples.py`) | *(add URL)* | Frappe `get_list` sanity check |

BTU-specific housekeeping remains in the app: `btu.btu_core.housekeeping.cleanup_transient_tasks`.
