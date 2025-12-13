#!/usr/bin/env python3
"""Check Python files for UNO rule compliance (One File, One Definition).

This script verifies that each Python file contains exactly one definitional unit
(class or function), excluding test files which may contain multiple test functions.

Interface:
    check_python.py [--filter <filter.py>] <dir>

    --filter <filter.py>: Optional filter script that takes a filename as input
                          and emits either the filename (not filtered) or empty
                          string (filtered). Filter script must exist outside
                          the .cursor directory.

    <dir>: Directory to check (defaults to current directory)
"""

import argparse
import ast
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from rich.console import Console

console = Console()


def count_definitions(tree: ast.Module) -> tuple[int, int]:
    """Count top-level classes and functions in an AST module.

    Returns:
        Tuple of (class_count, function_count)
    """
    class_count = 0
    function_count = 0

    # Only check top-level definitions (direct children of Module)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            # Only count public classes (not starting with _)
            class_count += 1
        elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            # Only count public functions (not starting with _)
            function_count += 1
        # Ignore other top-level statements (imports, assignments, etc.)

    return class_count, function_count


def check_file(file_path: Path, filter_fn: Callable[[Path], str] | None = None) -> tuple[bool, str]:
    """Check a single Python file for UNO compliance.

    Args:
        file_path: Path to Python file
        filter_fn: Optional filter function that returns filename if not filtered,
                   empty string if filtered

    Returns:
        Tuple of (is_compliant, error_message)
    """
    # Apply filter if provided
    if filter_fn:
        filtered = filter_fn(file_path)
        if not filtered:  # Empty string means filtered out
            return True, ""  # Filtered files are considered compliant

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error parsing file: {e}"

    if not isinstance(tree, ast.Module):
        return False, "File does not contain a valid Python module"

    class_count, function_count = count_definitions(tree)

    # UNO rule: exactly one definition (class OR function)
    total_definitions = class_count + function_count

    if total_definitions == 0:
        return True, ""  # Empty files or files with only private definitions are OK
    elif total_definitions == 1:
        return True, ""
    else:
        definitions = []
        if class_count > 0:
            definitions.append(f"{class_count} class(es)")
        if function_count > 0:
            definitions.append(f"{function_count} function(s)")
        return False, f"Contains {total_definitions} public definitions: {', '.join(definitions)}"


def load_filter_script(filter_path: Path) -> Callable[[Path], str]:
    """Load and return a filter function from a Python script.

    The filter script should define a function that takes a filename and returns
    either the filename (not filtered) or empty string (filtered).

    Args:
        filter_path: Path to filter script

    Returns:
        Filter function that takes Path and returns str
    """
    if not filter_path.exists():
        raise FileNotFoundError(f"Filter script not found: {filter_path}")

    # Read and execute filter script
    filter_code = filter_path.read_text(encoding="utf-8")
    filter_globals: dict = {}
    exec(filter_code, filter_globals)

    # Look for a function that might be the filter
    # Common names: filter, filter_file, should_include
    for name in ["filter", "filter_file", "should_include"]:
        if name in filter_globals and callable(filter_globals[name]):
            filter_func = filter_globals[name]

            def wrapper(file_path: Path, func=filter_func) -> str:
                result = func(str(file_path))
                return result if result else ""

            return wrapper

    # If no function found, try to use the script as a module that processes stdin
    # This allows filters to be simple scripts that read from stdin
    def stdin_filter(file_path: Path) -> str:
        result = subprocess.run(
            [sys.executable, str(filter_path), str(file_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""

    return stdin_filter


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check Python files for UNO rule compliance (One File, One Definition)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check current directory
  check_python.py .

  # Check specific directory
  check_python.py wks/api

  # Check with filter script
  check_python.py --filter /path/to/filter.py wks/api

Filter script interface:
  The filter script should take a filename as input (via sys.argv[1] or function argument)
  and emit either:
    - The filename (if file should be checked)
    - Empty string (if file should be skipped)
        """,
    )
    parser.add_argument(
        "--filter",
        type=Path,
        help="Optional filter script (outside .cursor directory) that filters files",
    )
    parser.add_argument("dir", type=Path, nargs="?", default=Path(), help="Directory to check")

    args = parser.parse_args()

    # Validate filter path (must exist outside .cursor)
    filter_fn = None
    if args.filter:
        if ".cursor" in args.filter.parts:
            console.print("[bold red]Error: Filter script must be outside .cursor directory[/bold red]")
            sys.exit(1)
        try:
            filter_fn = load_filter_script(args.filter)
        except Exception as e:
            console.print(f"[bold red]Error loading filter script: {e}[/bold red]")
            sys.exit(1)

    # Find all Python files
    target_dir = args.dir.resolve()
    if not target_dir.exists():
        console.print(f"[bold red]Error: Directory not found: {target_dir}[/bold red]")
        sys.exit(1)

    python_files = list(target_dir.rglob("*.py"))
    python_files = [f for f in python_files if "__pycache__" not in str(f)]

    if not python_files:
        console.print(f"[yellow]No Python files found in {target_dir}[/yellow]")
        sys.exit(0)

    # Check each file
    violations = []
    checked_count = 0

    for file_path in sorted(python_files):
        is_compliant, error_msg = check_file(file_path, filter_fn)
        if not is_compliant:
            violations.append((file_path, error_msg))
        if error_msg or is_compliant:  # Count files that were actually checked
            checked_count += 1

    # Report results
    if violations:
        console.print(f"\n[bold red]UNO Rule Violations ({len(violations)} files):[/bold red]\n")
        for file_path, error_msg in violations:
            rel_path = file_path.relative_to(target_dir)
            console.print(f"  [red]{rel_path}[/red]")
            console.print(f"    {error_msg}\n")
        console.print(f"[bold red]FAILED: {len(violations)} file(s) violate UNO rule[/bold red]")
        sys.exit(1)
    else:
        console.print(f"[bold green]PASSED: All {checked_count} file(s) comply with UNO rule[/bold green]")
        sys.exit(0)


if __name__ == "__main__":
    main()
