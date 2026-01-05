#!/usr/bin/env python3
"""Generate UNO defs evidence using lizard."""

import argparse
import json
import os
import sys
from glob import glob
from typing import Dict, List


SCHEMA = "cursorcult.defs.v1"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_existing(path: str) -> Dict:
    if not os.path.isfile(path):
        return {"schema": SCHEMA, "domains": {}, "files": 0, "defs": 0}
    try:
        data = json.loads(open(path, "r", encoding="utf-8").read())
    except Exception as e:
        fail(f"Failed to parse existing JSON: {e}")
    if not isinstance(data, dict):
        fail("Existing JSON must be an object.")
    if data.get("schema") != SCHEMA:
        fail(f"schema must be '{SCHEMA}'")
    if "domains" not in data or not isinstance(data["domains"], dict):
        fail("Existing JSON missing domains object.")
    return data


def collect_paths(patterns: List[str]) -> List[str]:
    results = set()
    for pattern in patterns:
        for path in glob(pattern, recursive=True):
            if os.path.isfile(path):
                results.add(path)
    return sorted(results)


def analyze_file(path: str) -> List[Dict]:
    try:
        import lizard
    except Exception as e:
        fail(f"lizard is required for generator.py: {e}")

    try:
        content = open(path, "r", encoding="utf-8", errors="replace").read()
    except Exception as e:
        fail(f"Failed to read {path}: {e}")

    info = lizard.analyze_file.analyze_source_code(path, content)
    locs = []
    for func in info.function_list:
        locs.append(
            {
                "kind": "function",
                "name": func.name,
                "lineno": func.start_line,
            }
        )
    locs.sort(key=lambda x: (x["lineno"], x["kind"], x["name"]))
    return locs


def recompute_aggregates(domains: Dict) -> Dict:
    total_files = 0
    total_defs = 0
    for domain in domains.values():
        files = domain.get("files", {})
        total_files += len(files)
        for record in files.values():
            total_defs += int(record.get("defs", 0))
    return {"files": total_files, "defs": total_defs}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate UNO defs evidence using lizard.")
    parser.add_argument("--glob", action="append", required=True, help="Glob pattern of files.")
    parser.add_argument("--domain", required=True, help="Domain name.")
    parser.add_argument("--output", required=True, help="Output JSON path (repo-relative).")
    args = parser.parse_args()

    output = args.output
    if os.path.isabs(output):
        fail("--output must be repo-relative.")

    data = load_existing(output)
    domains = data.setdefault("domains", {})

    files_map: Dict[str, Dict] = {}
    for path in collect_paths(args.glob):
        locs = analyze_file(path)
        files_map[path] = {"defs": len(locs), "locs": locs}

    domains[args.domain] = {"files": files_map}

    aggregates = recompute_aggregates(domains)
    data["files"] = aggregates["files"]
    data["defs"] = aggregates["defs"]

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
