#!/usr/bin/env python3
"""Evaluate UNO rule using defs evidence JSON."""

import argparse
import json
import os
import sys


SCHEMA = "cursorcult.defs.v1"


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    parts = normalized.split("/")
    if any(part in ("test", "tests") for part in parts[:-1]):
        return True
    filename = parts[-1]
    stem = filename.rsplit(".", 1)[0]
    return stem.startswith("test_") or stem.endswith("_test")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate UNO rule using defs evidence.")
    parser.add_argument("--domain", help="Evaluate only a single domain.")
    parser.add_argument("path", help="Path to defs.json (or configured output file).")
    args = parser.parse_args()

    if not os.path.isfile(args.path):
        fail(f"File not found: {args.path}")

    try:
        data = json.loads(open(args.path, "r", encoding="utf-8").read())
    except Exception as e:
        fail(f"Failed to parse JSON: {e}")

    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        fail(f"schema must be '{SCHEMA}'")

    domains = data.get("domains")
    if not isinstance(domains, dict):
        fail("domains must be an object.")

    selected = domains
    if args.domain:
        if args.domain not in domains:
            fail(f"domain not found: {args.domain}")
        selected = {args.domain: domains[args.domain]}

    violations = []
    for domain_name, domain in selected.items():
        files = domain.get("files", {})
        for path, record in files.items():
            defs_count = record.get("defs")
            if not isinstance(defs_count, int):
                continue
            if defs_count == 0:
                continue
            if is_test_path(path):
                continue
            if defs_count != 1:
                violations.append((path, defs_count, domain_name))

    if violations:
        print("UNO violations:")
        for path, defs_count, domain_name in violations:
            print(f"- {path} (defs={defs_count}, domain={domain_name})")
        return 1

    print("PASS: UNO check succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
