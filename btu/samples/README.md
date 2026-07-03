# BTU samples

Functions and classes you can reference from a **BTU Task** `function_string` field.

| Module | Symbols |
|--------|---------|
| `aware.py` | `btu_aware_example1` — BTU-aware class with Task Components |
| `simple.py` | `ordinary_function` — plain callable with no BTU imports |
| `errors.py` | `wait_then_throw_error` — simulates a task failure |

Legacy import path `btu.examples` re-exports these symbols.

Create a BTU Task with **Function** set to e.g. `btu.samples.simple.ordinary_function` and pass arguments as a JSON dict.
