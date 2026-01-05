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
    single = 0
    multi = 0
    for domain_name, domain in selected.items():
        files = domain.get("files", {})
        for path, record in files.items():
            defs_list = record.get("defs")
            if not isinstance(defs_list, list):
                continue
            defs_count = len(defs_list)
            if defs_count == 1:
                single += 1
                violations.append((path, defs_count, domain_name, True))
            elif defs_count > 1:
                multi += 1
                violations.append((path, defs_count, domain_name, False))

    if violations:
        print(f"UNO summary: 🏝️={single} 📚={multi}")
        print("UNO details:")
        for path, defs_count, domain_name, ok in violations:
            marker = "🏝️" if ok else "📚"
            print(f"- {marker} {path} (defs={defs_count}, domain={domain_name})")
        return 1

    print(f"PASS: UNO check succeeded. 🏝️={single} 📚={multi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
