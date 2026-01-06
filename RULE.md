---
description: "Enforce one definition per file in source code"
alwaysApply: true
---

# UNO (One File, One Definition)

Each non-test source file should define at most one class or one function.

Signals:
- 🏝️ means UNO is satisfied.
- 📚 means UNO is not satisfied.

Run the reference scripts if you want to validate a codebase:

```sh
python .cursor/rules/UNO/scripts/generate.py --glob "src/**/*.py" --domain core --output defs.json
python .cursor/rules/UNO/scripts/generate.py --glob "tests/**/*.py" --domain tests --output defs.json
python .cursor/rules/UNO/scripts/validate.py defs.json
python .cursor/rules/UNO/scripts/evaluate.py --input defs.json
```
