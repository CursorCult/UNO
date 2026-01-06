import json
import os
import subprocess
import sys
import tempfile
import textwrap


def rule_dir() -> str:
    env_dir = os.environ.get("UNO_RULE_DIR")
    if env_dir:
        return env_dir
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_generate(tmpdir: str) -> dict:
    defs_path = os.path.join(tmpdir, "defs.json")
    pattern = os.path.join(tmpdir, "**", "*.py")
    script = os.path.join(rule_dir(), "scripts", "generate.py")
    subprocess.run(
        [
            sys.executable,
            script,
            "--glob",
            pattern,
            "--domain",
            "core",
            "--output",
            defs_path,
        ],
        check=True,
    )
    with open(defs_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_top_level_defs_only() -> None:
    sample = textwrap.dedent(
        """
        class C:
            def method(self):
                return 1

        def f():
            def inner():
                return 2
            return inner()
        """
    ).lstrip()

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "sample.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(sample)

        data = run_generate(tmpdir)
        domains = data.get("domains", {})
        files = domains.get("core", {}).get("files", {})
        record = files.get(path, {})
        defs_list = record.get("defs", [])

        names = {item.get("name") for item in defs_list}
        kinds = {item.get("kind") for item in defs_list}
        assert names == {"C", "f"}
        assert kinds == {"class", "function"}
