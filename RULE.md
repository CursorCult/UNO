---
description: "Enforce one definition per file in source code"
alwaysApply: true
---

# UNO Pattern (One File, One Definition)

The UNO Pattern is language agnostic and applies to non-test source code. It enforces a strict rule: one file, one definitional unit. A module may contain one class or one function, but never more. No helpers, no side-utilities, no mixed responsibilities.

This isolates behavior, reduces cognitive load, and keeps dependency boundaries explicit. It also makes Git diffs unambiguous: when a file changes, you know exactly which unit changed, with no risk of collateral edits hiding in the same module.

The only exception is test files, which may group multiple tests as needed for clarity and coverage.

UNO does not require naming consistency between a file and the function or class it contains. Choose whatever naming convention fits your language or project; the constraint is about count and responsibility, not names.

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
