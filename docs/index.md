## Background Tasks Unleashed (BTU)
Background Tasks Unleashed is:

* a <a href="https://frappeframework.com" target="_blank">Frappe Framework</a> application for Task Scheduling and Automation.
* a tool for running tasks or processes automatically, on a repeating schedule, in the background of your Frappe web application.
* a robust alternative to the out-of-the-box Scheduled Job Types feature in Frappe v13+
* an pair of open source projects on GitHub
  * **BTU**: [https://github.com/Datahenge/btu](https://github.com/Datahenge/btu)
  * **BTU Scheduler** : [https://github.com/Datahenge/btu_scheduler_daemon](https://github.com/Datahenge/btu_scheduler_daemon)

### Table of Contents
* [Installation](https://datahenge.github.io/btu/installation.html)
* [Scheduler Configuration](https://datahenge.github.io/btu/configuration.html)

### User Guides
  * [Web Interface](https://datahenge.github.io/btu/guide_web.html)
  * [Command Line Interface](https://datahenge.github.io/btu/guide_cli.html)
  * [Automatic Report Delivery](https://datahenge.github.io/btu/guide_auto_report.html)

### Frequently Asked Questions (FAQ)
Answers to frequently asked questions [can be found here.](https://datahenge.github.io/btu/faq.html)

### Technical Design
[Technical design](technical_design.md) describes why BTU is split across a Frappe app and a scheduler daemon, and the product constraints behind Run Later and Redis RPC. Maintainer ADRs: [docs/dev/adr/](dev/adr/README.md).

### Developer
* [Repository layout](dev/repository_layout.md)
* [Archived utility scripts (Gists)](dev/gists.md)
