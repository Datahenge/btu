## Background Tasks Unleashed (BTU) v14

For details, please read the project's **[Official Documentation](https://datahenge.github.io/btu/)**.

If you're looking for its companion application, the **BTU Scheduler**, that project is maintained <a href="https://github.com/Datahenge/btu_scheduler_daemon" target='_blank'>on a separate GitHub site</a>.

### What is this?
Background Tasks Unleashed is:

* a [Frappe Framework](https://github.com/frappe) application for Task Scheduling and Automation.

* a tool for running tasks or processes *automatically*, on a repeating schedule, in the background of your Frappe web application.

* a robust alternative to the out-of-the-box **`Scheduled Job Types`** feature in Frappe v13+

<img style="text-align: center;" src="https://datahenge.github.io/btu/images/btu_screenshot_workspace_1.png" alt="BTU Workspace" title="image Title" width="800"/>

### Capabilities
Using only your web browser, take full control of the BTU application.  No need to SSH and modify `hooks.py`.

* **Tasks** organize your reusable jobs, enabling you to run any Python function (standard or custom) and pass your own arguments.
* **Schedules** will run Tasks in the background, at any cadence required (FYI, we can do cron...*with timezones!*)
* **Logs** give you visibility into your Task history.  Not just success or fail, but the *complete standard output and errors*.

You can also:

* Run any Task on-demand.
* When a scheduled Task completes, automatically receive an email notification (including CC and BCC)
* Use an included CLI application to interact with the BTU from a shell terminal, instead of your web browser.

----
### Installation
A complete [Installation Guide](https://datahenge.github.io/btu/installation.html) is available on BTU's GitHub Pages site.

### Copyright and License
* Background Tasks Unleashed (BTU) is licensed MIT. (*See LICENSE.md file*)
* Copyright 2022, Datahenge LLC
* Maintainer: Brian Pond <brian@datahenge.com>
