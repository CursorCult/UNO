#!/usr/bin/env python3
"""Validate UNO defs evidence JSON."""

import argparse
import json
import os
import sys


SCHEMA = "cursorcult.defs.v1"
ALLOWED_TOP_KEYS = {"schema", "domains", "files", "defs"}
ALLOWED_DOMAIN_KEYS = {"files"}
ALLOWED_FILE_KEYS = {"defs", "locs"}
ALLOWED_LOC_KEYS = {"kind", "name", "lineno"}
ALLOWED_KINDS = {"function", "class"}


def fail(message: str) -> None:
    print(f"INVALID: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_loc(loc: dict, path: str) -> None:
    extra = set(loc.keys()) - ALLOWED_LOC_KEYS
    if extra:
        fail(f"{path}: unexpected loc keys: {sorted(extra)}")
    kind = loc.get("kind")
    name = loc.get("name")
    lineno = loc.get("lineno")
    if kind not in ALLOWED_KINDS:
        fail(f"{path}: loc.kind must be one of {sorted(ALLOWED_KINDS)}")
    if not isinstance(name, str) or not name.strip():
        fail(f"{path}: loc.name must be a non-empty string")
    if not isinstance(lineno, int) or lineno < 1:
        fail(f"{path}: loc.lineno must be an integer >= 1")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate UNO defs evidence JSON.")
    parser.add_argument("path", help="Path to defs.json (or configured output file).")
    args = parser.parse_args()

    if not os.path.isfile(args.path):
        fail(f"File not found: {args.path}")

    try:
        data = json.loads(open(args.path, "r", encoding="utf-8").read())
    except Exception as e:
        fail(f"Failed to parse JSON: {e}")

    if not isinstance(data, dict):
        fail("Top-level JSON must be an object.")

    extra_top = set(data.keys()) - ALLOWED_TOP_KEYS
    if extra_top:
        fail(f"Unexpected top-level keys: {sorted(extra_top)}")

    if data.get("schema") != SCHEMA:
        fail(f"schema must be '{SCHEMA}'")

    domains = data.get("domains")
    if not isinstance(domains, dict) or not domains:
        fail("domains must be a non-empty object.")

    files_total = data.get("files")
    defs_total = data.get("defs")
    if not isinstance(files_total, int) or files_total < 0:
        fail("files must be an integer >= 0.")
    if not isinstance(defs_total, int) or defs_total < 0:
        fail("defs must be an integer >= 0.")

    expected_domains = os.environ.get("CC_DOMAINS")
    if expected_domains:
        expected_set = {d for d in expected_domains.split(",") if d}
        actual_set = set(domains.keys())
        if actual_set != expected_set:
            fail(f"domains must match .CCUNO: {sorted(expected_set)}")

    seen_paths = set()
    computed_files = 0
    computed_defs = 0

    for domain_name, domain in domains.items():
        if not isinstance(domain, dict):
            fail(f"{domain_name}: domain must be an object.")
        extra_domain = set(domain.keys()) - ALLOWED_DOMAIN_KEYS
        if extra_domain:
            fail(f"{domain_name}: unexpected domain keys: {sorted(extra_domain)}")
        files = domain.get("files")
        if not isinstance(files, dict):
            fail(f"{domain_name}: files must be an object.")

        for path, record in files.items():
            if path in seen_paths:
                fail(f"Duplicate file path across domains: {path}")
            seen_paths.add(path)
            if not isinstance(record, dict):
                fail(f"{path}: file record must be an object.")
            extra_file = set(record.keys()) - ALLOWED_FILE_KEYS
            if extra_file:
                fail(f"{path}: unexpected file keys: {sorted(extra_file)}")
            defs_count = record.get("defs")
            locs = record.get("locs")
            if not isinstance(defs_count, int) or defs_count < 0:
                fail(f"{path}: defs must be an integer >= 0.")
            if not isinstance(locs, list):
                fail(f"{path}: locs must be a list.")
            if defs_count != len(locs):
                fail(f"{path}: defs must equal len(locs).")
            for loc in locs:
                if not isinstance(loc, dict):
                    fail(f"{path}: each loc must be an object.")
                validate_loc(loc, path)
            computed_files += 1
            computed_defs += defs_count

    if computed_files != files_total:
        fail(f"files must equal computed total ({computed_files}).")
    if computed_defs != defs_total:
        fail(f"defs must equal computed total ({computed_defs}).")

    print("OK: defs evidence is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
