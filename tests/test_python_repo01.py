import json
import os
import shutil
import subprocess
import sys
import tempfile
import pytest

def require_tree_sitter() -> None:
    try:
        import tree_sitter_languages  # noqa: F401
    except Exception:
        pytest.skip("tree_sitter_languages is required for UNO tests.")


def rule_dir() -> str:
    env_dir = os.environ.get("UNO_RULE_DIR")
    if env_dir:
        return env_dir
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_generate(tmpdir: str) -> dict:
    defs_path = "defs.json"
    pattern = os.path.join("src", "**", "*.py")
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
        cwd=tmpdir,
    )
    with open(os.path.join(tmpdir, defs_path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_top_level_defs_only() -> None:
    require_tree_sitter()
    with tempfile.TemporaryDirectory() as tmpdir:
        fixture_dir = os.path.join(
            os.path.dirname(__file__), "fixtures", "python", "repo01"
        )
        shutil.copytree(fixture_dir, tmpdir, dirs_exist_ok=True)
        path = os.path.join("src", "sample.py")

        data = run_generate(tmpdir)
        domains = data.get("domains", {})
        files = domains.get("core", {}).get("files", {})
        record = files.get(path, {})
        defs_list = record.get("defs", [])

        assert set(files.keys()) == {path}
        names = {item.get("name") for item in defs_list}
        kinds = {item.get("kind") for item in defs_list}
        assert names == {"C", "f"}
        assert kinds == {"class", "function"}
