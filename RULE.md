---
description: "Enforce one definition per file in source code"
alwaysApply: true
---

# UNO Pattern (One File, One Definition)

The UNO Pattern is language agnostic and applies to non-test source code. It enforces a strict rule: one file, one definitional unit. A module may contain one class or one function, but never more. No helpers, no side-utilities, no mixed responsibilities.

This isolates behavior, reduces cognitive load, and keeps dependency boundaries explicit. It also makes Git diffs unambiguous: when a file changes, you know exactly which unit changed, with no risk of collateral edits hiding in the same module.

The only exception is test files, which may group multiple tests as needed for clarity and coverage.

UNO also requires naming consistency between a file and the definition it contains. The file name (without extension) must match the definition name using your project’s naming convention (e.g., `UserProfile` in `user_profile.py`).

## Signals

- 🏝️ in any chat or attached to a comment or code snippet indicates UNO is satisfied.
- 📚 in any chat or attached to a comment or code snippet indicates UNO is not satisfied.

## Evidence format (cursorcult.defs.v1)

Programmatic evaluation uses a shared `defs.json` (name configurable) with domain grouping:

```json
{
  "schema": "cursorcult.defs.v1",
  "domains": {
    "core": {
      "files": {
        "src/a.py": {
          "defs": [{"kind": "function", "name": "f", "lineno": 10}]
        }
      },
      "single": 1,
      "multi": 0
    }
  },
  "single": 1,
  "multi": 0
}
```

Default generator (`--glob` is repeatable):

```text
python .cursor/rules/UNO/scripts/generator.py --glob "src/**/*.py" --domain core --output defs.json
```

## Examples (Python)

Allowed: one definitional unit per file.

`user.py`
```py
class User:
    def __init__(self, name: str):
        self.name = name
```

`compute_tax.py`
```py
def compute_tax(amount: float, rate: float) -> float:
    return amount * rate
```

Not allowed: multiple definitions in one file.

`user_and_helpers.py`
```py
class User:
    ...

def normalize_name(name: str) -> str:
    ...
```

Allowed exception: tests may group multiple cases.

`test_user.py`
```py
def test_user_creation():
    ...

def test_user_display_name():
    ...
```
