### User Guide:  Command Line Interface

Along with the background scheduler daemon, BTU ships with a small CLI program.\

The name of this program is `btu`, and is usually found in the directory `/usr/local/bin`

<img src="https://github.com/Datahenge/btu/blob/version-13/docs/images/btu_cli_1.png" width="75%" height="75%" />

### Available Commands

* `list_jobs`
   * Prints a list of Python RQ jobs currently found in Redis.
* `list-tasks`
    * Shows all Task Schedules that BTU is waiting to queue
    * **Very** useful for validating that everything you *expect* to happen, is actually scheduled.
* `print_config`
    * Prints the keys and values in `/etc/btu_scheduler/btu_scheduler.toml` to the terminal.
