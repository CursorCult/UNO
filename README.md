# UNO

The UNO Pattern: one file == one definitional unit.

**Install**

```sh
pipx install cursorcult
cursorcult link UNO
```

Rule file format reference: https://cursor.com/docs/context/rules#rulemd-file-format

**Programmatic evaluation (.CCUNO)**

Create a `.CCUNO` at repo root with full command lines. Generators must include
`--domain` and `--output`, and the evaluator must include `--input`. All
generators must write to the same output file (typically `defs.json`).

Example:

```text
python .cursor/rules/UNO/scripts/generate.py --glob "src/**/*.py" --domain core --output defs.json
python .cursor/rules/UNO/scripts/generate.py --glob "tests/**/*.py" --domain tests --output defs.json
python .cursor/rules/UNO/scripts/evaluate.py --input defs.json
```

The output schema is `cursorcult.defs.v1`:

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

**Pre-commit hook**

UNO ships a pre-commit hook you can install to run evaluation on every commit:

```sh
cp .cursor/rules/UNO/scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**When to use**

- You want modules to be maximally focused and easy to reason about.
- You want diffs to map to a single behavioral change.
- You’re trying to keep dependency boundaries explicit and avoid hidden helpers.
- You’re working in a codebase where “utility creep” is a recurring problem.

**Guidelines**

- Common use-case: keep production files to one definition each while letting test files group multiple tests in a file.

**Signals**

- 🏝️ means the code or note is satisfying UNO.
- 📚 means the code or note is not satisfying UNO.

**What it enforces**

- Each non-test source file defines exactly one class *or* one function.
- No extra helpers, side-utilities, or mixed responsibilities in the same module.
- The file name matches the definition name (following your project’s naming convention).
- Test files are the only allowed exception for grouping.

**Checker options**

- `UNO/scripts/check_python.py` supports `--loose` to allow case-insensitive name matching and ignore underscores.
- Progress output is on by default; use `--no-progress` to disable.

**Reference scripts**

UNO includes reference implementations you can run directly:

```sh
python .cursor/rules/UNO/scripts/generate.py --glob "src/**/*.py" --domain core --output defs.json
python .cursor/rules/UNO/scripts/generate.py --glob "tests/**/*.py" --domain tests --output defs.json
python .cursor/rules/UNO/scripts/validate.py defs.json
python .cursor/rules/UNO/scripts/evaluate.py --input defs.json
```

The generate script uses tree-sitter for all supported languages.
Install dependencies with:

```sh
pipx install tree_sitter tree-sitter-languages
```

**Credits**

- Developed by Will Wieselquist. Anyone can use it.

**See also**

- https://github.com/CursorCult/EzGrep.git
