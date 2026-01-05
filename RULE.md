---
description: "Enforce one definition per file in source code"
alwaysApply: true
---

# UNO (One File, One Definition)

Each non-test source file should define exactly one class or one function. Keep files focused and avoid bundled helpers.

## Signals

- 🏝️ indicates UNO is satisfied.
- 📚 indicates UNO is not satisfied.

## Use and test it

You can run the reference scripts directly:

```sh
python .cursor/rules/UNO/scripts/generate.py --glob "src/**/*.py" --domain core --output defs.json
python .cursor/rules/UNO/scripts/generate.py --glob "tests/**/*.py" --domain tests --output defs.json
python .cursor/rules/UNO/scripts/validate.py defs.json
python .cursor/rules/UNO/scripts/evaluate.py --input defs.json
```

The generator uses tree-sitter for all supported languages:

```sh
pipx install tree_sitter tree_sitter_languages
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
