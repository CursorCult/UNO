# UNO

The UNO Pattern: one file == one definitional unit.

**Install**

```sh
pipx install cursorcult
cursorcult link UNO
```

Rule file format reference: https://cursor.com/docs/context/rules#rulemd-file-format

**Programmatic evaluation (.CCUNO)**

Create a `.CCUNO` at repo root with eval args on line 1 and generator commands on
lines 2..N. Generators must include `--domain` and `--output`, and all generators
must share the same output file (typically `defs.json`). `--glob` is repeatable.

Example:

```text
--
python .cursor/rules/UNO/scripts/generator.py --glob "src/**/*.py" --domain core --output defs.json
python .cursor/rules/UNO/scripts/generator.py --glob "tests/**/*.py" --domain tests --output defs.json
```

The output schema is `cursorcult.defs.v1` and must include required aggregates:

```json
{
  "schema": "cursorcult.defs.v1",
  "domains": {
    "core": {
      "files": {
        "src/a.py": {
          "defs": 1,
          "locs": [{"kind": "function", "name": "f", "lineno": 10}]
        }
      }
    }
  },
  "files": 1,
  "defs": 1
}
```

**When to use**

- You want modules to be maximally focused and easy to reason about.
- You want diffs to map to a single behavioral change.
- You’re trying to keep dependency boundaries explicit and avoid hidden helpers.
- You’re working in a codebase where “utility creep” is a recurring problem.

**What it enforces**

- Each non-test source file defines exactly one class *or* one function.
- No extra helpers, side-utilities, or mixed responsibilities in the same module.
- The file name matches the definition name (following your project’s naming convention).
- Test files are the only allowed exception for grouping.

**Checker options**

- `UNO/scripts/check_python.py` supports `--loose` to allow case-insensitive name matching and ignore underscores.
- Progress output is on by default; use `--no-progress` to disable.

**Credits**

- Developed by Will Wieselquist. Anyone can use it.

**See also**

- https://github.com/CursorCult/EzGrep.git
