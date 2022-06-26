### Part One: Scheduler Configuration

No matter where you save the `btu-daemon` binary file, the configuration data is *always* stored in this directory:

```
/etc/btu_scheduler/
```

The main configuration file we care about is named **`btu_scheduler.toml`**  (full path = `/etc/btu_scheduler/btu_scheduler.toml`

This configuration file uses the [TOML data format](https://toml.io/en/).  It's equivalent to formats like JSON or YAML.

Below is an example of what `btu_scheduler.toml` should look like:

```toml
name = "BTU Scheduler Daemon"
environment_name = "DEV"
full_refresh_internal_secs = 900
scheduler_polling_interval=60
time_zone_string="America/Los_Angeles"
tracing_level="INFO"

# Email Setup
email_address_from = "my_email_account@datahenge.com"
email_host_name = "smtp.my_mail_server.com"
email_host_port = 587
email_account_name = "my_email_account@datahenge.com"
email_account_password  = "my_email_password"

# Email Features
email_addresses = [ "brian@datahenge.com" ]
email_on_level="INFO"
email_when_queuing=true

# MySQL
mysql_user = "my_sql_user_name"
mysql_password = "my_sql_account_password"
mysql_host = "localhost"
mysql_port = 3313
mysql_database = "erpnext_db_13"

# RQ
rq_host = "127.0.0.1"
rq_port = 11000
socket_path = "/tmp/btu_scheduler.sock"
socket_file_group_owner = "erpnext_group"
webserver_ip = "127.0.0.1"
webserver_port = 8000
webserver_token = "token abcdefghij12345:lmnopq678901234"
```
