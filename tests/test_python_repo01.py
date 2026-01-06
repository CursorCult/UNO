import json
import os
import subprocess
import sys


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


def test_top_level_defs_only(repo_fixture) -> None:
    tmpdir = repo_fixture("python", "repo01")
    sample_path = os.path.join("src", "sample.py")
    init_path = os.path.join("src", "__init__.py")

    data = run_generate(str(tmpdir))
    domains = data.get("domains", {})
    files = domains.get("core", {}).get("files", {})
    sample_record = files.get(sample_path, {})
    init_record = files.get(init_path, {})
    sample_defs = sample_record.get("defs", [])
    init_defs = init_record.get("defs", [])

    assert set(files.keys()) == {sample_path, init_path}
    names = {item.get("name") for item in sample_defs}
    kinds = {item.get("kind") for item in sample_defs}
    assert names == {"C", "f"}
    assert kinds == {"class", "function"}
    assert init_defs == []
