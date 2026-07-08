# Writing task functions

## Function path

BTU Task **Function** must be a string:

```
myapp.my_module.my_function
```

Function objects are not accepted (15.1+).

## Signature

Tasks receive kwargs from **Function Arguments**. No special base class required.

## Return values

Return normally on success. Raise on failure — BTU captures traceback in Task Log.

Optional: return `btu.Result` for structured messages in custom wrappers.

## Logging

Use Python `logging` or `frappe.logger("btu")`. Stdout/stderr are captured into Task Log.

## Samples

| Path | Purpose |
|------|---------|
| `btu.samples.weather.get_current_weather` | End-to-end demo — prints *and* returns (see [Your first task](../get-started/first-task.md)) |
| `btu.samples.simple.ordinary_function` | Minimal plain callable |
| `btu.samples.errors.wait_then_throw_error` | Failure testing |
| `btu.diagnostics.smoke.ping_with_wait` | Worker smoke test |

## Packaging

Custom functions must live in an app installed on the bench where workers run.
