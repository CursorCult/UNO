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
    parser.add_argument("--input", help="Path to defs.json (or configured output file).")
    parser.add_argument("path", nargs="?", help="Path to defs.json (or configured output file).")
    args = parser.parse_args()

    input_path = args.input or args.path
    if not input_path:
        fail("Missing --input.")
    if not os.path.isfile(input_path):
        fail(f"File not found: {input_path}")

    try:
        data = json.loads(open(input_path, "r", encoding="utf-8").read())
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

    any_bad = False
    for domain_name in sorted(selected.keys()):
        domain = selected[domain_name]
        files = domain.get("files", {})
        good = 0
        bad = 0
        violators = []
        for path, record in files.items():
            defs_list = record.get("defs")
            if not isinstance(defs_list, list):
                continue
            defs_count = len(defs_list)
            if defs_count == 1:
                good += 1
            else:
                bad += 1
                violators.append((path, defs_list))
        marker = "check" if bad == 0 else "x"
        print(f"{marker} : {domain_name} : 🏝️ {good} 📚 {bad}")
        for path, defs_list in sorted(violators, key=lambda item: item[0]):
            print(f"  {path} : {json.dumps(defs_list, ensure_ascii=True)}")
        if bad:
            any_bad = True

    return 1 if any_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
