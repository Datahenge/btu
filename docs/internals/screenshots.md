# Screenshot conventions

Desk and CLI screenshots live in [`docs/assets/images/`](../assets/images/).

## Adding images

1. Save PNG or WebP files with descriptive names, e.g.:
   - `desk-btu-configuration.png`
   - `desk-btu-task-form.png`
   - `desk-btu-task-schedule-cron.png`
   - `desk-btu-task-log-detail.png`
   - `desk-btu-run-later-list.png`
   - `cli-btu-py-config-show.png`
2. Reference in markdown:

```markdown
<figure class="btu-screenshot" markdown="span">
![BTU Configuration form](../assets/images/desk-btu-configuration.png)
<figcaption>BTU Configuration — ping scheduler and email defaults</figcaption>
</figure>
```

3. Run `mkdocs serve` locally to verify layout.

## Priority pages for screenshots

| Page | Suggested capture |
|------|-------------------|
| [Desk overview](../guides/desk/index.md) | BTU_Core workspace |
| [BTU Configuration](../guides/desk/configuration.md) | Full form + ping button |
| [BTU Task](../guides/desk/task.md) | Task form with function path |
| [BTU Task Schedule](../guides/desk/task-schedule.md) | Cron + timezone fields |
| [BTU Task Log](../guides/desk/task-log.md) | Log with stdout/stderr |
| [BTU Run Later](../guides/desk/run-later.md) | List + document detail |
| [Install scheduler](../operations/install-scheduler.md) | `btu-py config show` terminal |

Share screenshots in chat or commit directly to `docs/assets/images/` — either works.

## Logo

Place **Datahenge** or **BTU** logo files in `docs/assets/`:

- `logo.svg` — header (light background); used when present
- `favicon.png` — browser tab icon (optional)

Until a BTU-specific mark exists, the Datahenge logo is fine. Update `theme.logo` in [`mkdocs.yml`](https://github.com/Datahenge/btu/blob/version-15/mkdocs.yml) after adding files.
