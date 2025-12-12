# UNO

The UNO Pattern: one file == one definitional unit.

**Install**

```sh
pipx install cursorcult
cursorcult link UNO
```

Rule file format reference: https://cursor.com/docs/context/rules#rulemd-file-format

**When to use**

- You want modules to be maximally focused and easy to reason about.
- You want diffs to map to a single behavioral change.
- You’re trying to keep dependency boundaries explicit and avoid hidden helpers.
- You’re working in a codebase where “utility creep” is a recurring problem.

**What it enforces**

- Each non-test source file defines exactly one class *or* one function.
- No extra helpers, side-utilities, or mixed responsibilities in the same module.
- Test files are the only allowed exception for grouping.

**Credits**

- Developed by Will Wieselquist. Anyone can use it.

**See also**

- https://github.com/CursorCult/EzGrep.git
