# Upgrade

## BTU 15.2.0

Run after upgrading the Frappe app:

```bash
bench --site YOUR_SITE migrate
bench restart
```

### Email configuration change

BTU Configuration no longer stores SMTP settings. Notifications use a standard Frappe **Email Account**. Migration patches move existing SMTP data on `bench migrate`.

After migrate:

1. Open **BTU Configuration** → confirm **Default Email Account**.
2. Send a test notification if needed.

### BTU Queue DocType removed

Queue names now come from bench worker configuration (`common_site_config.json`), not a BTU Queue DocType. Migration removes old BTU Queue records.

### Scheduler offline saves

BTU Task Schedule documents save even when the scheduler daemon is unreachable; a warning is shown instead of blocking the save.

## Scheduler upgrades

Upgrade the scheduler package separately:

```bash
cd btu_scheduler_py
git pull
pip install -e .
# restart btu-py run-daemon
```

When Redis RPC or protocol changes land in both repos, upgrade **app and scheduler together**. See [Version policy](version-policy.md).

## Redis RPC migration (15.1.x)

If upgrading from a Unix-socket scheduler:

1. Upgrade BTU app to 15.1+.
2. Upgrade scheduler to a Redis-RPC-capable `btu_scheduler_py` build.
3. Remove Unix-socket-only configuration; control plane is Redis-only.

See [Redis RPC protocol](../reference/redis-rpc.md).
