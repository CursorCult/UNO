---
description: "Enforce one definition per file in source code"
alwaysApply: true
---

# UNO (One File, One Definition)

A file that satisfies UNO should define at most one class or one function.

Signals:
- 🏝️ means UNO is satisfied.
- 📚 means UNO is not satisfied.

## When it applies

UNO applies to any code source that is referenced in the `.CCUNO` file, which must exist in a parent directory.

1. When you are writing new code, you should obey UNO. 
2. When you find code that does not obey UNO and is referenced in `.CCUNO`, refactor it.

The scripts referenced in `.CCUNO` are used to check the codebase for conformance:
```
cursorcult eval UNO
```

New source directories must be referenced in `.CCUNO` for the rule check to apply. 

## Scripts

UNO provides a reference `generate` and `evaluate` script and the canonical `validate` script.

- `scripts/generate.py` - generates `defs.json` definition listing file
- `scripts/validate.py defs.json` - validates proper schema adherence
- `scripts/evaluate.py --input defs.json` - evaluates rule satisfaction

A standard setup for `.CCUNO` would use this `generate.py` and `evaluate.py`.
The provided `validate.py` is always used.

To call these scripts directly, you will need a supported python version with `tree-sitter` available.

If you use `cursorcult eval UNO` (recommended), then `tree-sitter` is installed with `cursorcult`.

You may also want to install the `scripts/pre-commit` git hook.

## See Also

See the companion `./README.md` for:

- installing the git hook, 
- setting up the `.CCUNO` file,
- `defs.json` schema.
