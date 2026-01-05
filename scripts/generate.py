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
        return {"schema": SCHEMA, "domains": {}, "single": 0, "multi": 0}
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
        fail(f"lizard is required for generate.py: {e}")

    try:
        content = open(path, "r", encoding="utf-8", errors="replace").read()
    except Exception as e:
        fail(f"Failed to read {path}: {e}")

    info = lizard.analyze_file.analyze_source_code(path, content)
    defs_list = []
    for func in info.function_list:
        defs_list.append(
            {
                "kind": "function",
                "name": func.name,
                "lineno": func.start_line,
            }
        )
    defs_list.sort(key=lambda x: (x["lineno"], x["kind"], x["name"]))
    return defs_list


def recompute_aggregates(domains: Dict) -> Dict:
    total_single = 0
    total_multi = 0
    for domain in domains.values():
        files = domain.get("files", {})
        domain_single = 0
        domain_multi = 0
        for record in files.values():
            defs_list = record.get("defs", [])
            if isinstance(defs_list, list):
                count = len(defs_list)
                if count == 1:
                    domain_single += 1
                elif count > 1:
                    domain_multi += 1
        domain["single"] = domain_single
        domain["multi"] = domain_multi
        total_single += domain_single
        total_multi += domain_multi
    return {"single": total_single, "multi": total_multi}


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
        defs_list = analyze_file(path)
        files_map[path] = {"defs": defs_list}

    domains[args.domain] = {"files": files_map}

    aggregates = recompute_aggregates(domains)
    data["single"] = aggregates["single"]
    data["multi"] = aggregates["multi"]

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
