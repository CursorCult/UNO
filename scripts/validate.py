#!/usr/bin/env python3
"""Validate UNO defs evidence JSON."""

import argparse
import json
import os
import sys


SCHEMA = "cursorcult.defs.v1"
ALLOWED_TOP_KEYS = {"schema", "domains", "single", "multi"}
ALLOWED_DOMAIN_KEYS = {"files", "single", "multi"}
ALLOWED_FILE_KEYS = {"defs"}
ALLOWED_DEF_KEYS = {"kind", "name", "lineno"}
ALLOWED_KINDS = {"function", "class"}


def fail(message: str) -> None:
    print(f"INVALID: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_def(defn: dict, path: str) -> None:
    extra = set(defn.keys()) - ALLOWED_DEF_KEYS
    if extra:
        fail(f"{path}: unexpected def keys: {sorted(extra)}")
    kind = defn.get("kind")
    name = defn.get("name")
    lineno = defn.get("lineno")
    if kind not in ALLOWED_KINDS:
        fail(f"{path}: def.kind must be one of {sorted(ALLOWED_KINDS)}")
    if not isinstance(name, str) or not name.strip():
        fail(f"{path}: def.name must be a non-empty string")
    if not isinstance(lineno, int) or lineno < 1:
        fail(f"{path}: def.lineno must be an integer >= 1")


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

    single_total = data.get("single")
    multi_total = data.get("multi")
    if not isinstance(single_total, int) or single_total < 0:
        fail("single must be an integer >= 0.")
    if not isinstance(multi_total, int) or multi_total < 0:
        fail("multi must be an integer >= 0.")

    expected_domains = os.environ.get("CC_DOMAINS")
    if expected_domains:
        expected_set = {d for d in expected_domains.split(",") if d}
        actual_set = set(domains.keys())
        if actual_set != expected_set:
            fail(f"domains must match .CCUNO: {sorted(expected_set)}")

    seen_paths = set()
    computed_single = 0
    computed_multi = 0

    for domain_name, domain in domains.items():
        if not isinstance(domain, dict):
            fail(f"{domain_name}: domain must be an object.")
        extra_domain = set(domain.keys()) - ALLOWED_DOMAIN_KEYS
        if extra_domain:
            fail(f"{domain_name}: unexpected domain keys: {sorted(extra_domain)}")
        files = domain.get("files")
        if not isinstance(files, dict):
            fail(f"{domain_name}: files must be an object.")
        domain_single = domain.get("single")
        domain_multi = domain.get("multi")
        if not isinstance(domain_single, int) or domain_single < 0:
            fail(f"{domain_name}: single must be an integer >= 0.")
        if not isinstance(domain_multi, int) or domain_multi < 0:
            fail(f"{domain_name}: multi must be an integer >= 0.")

        domain_single_calc = 0
        domain_multi_calc = 0

        for path, record in files.items():
            if path in seen_paths:
                fail(f"Duplicate file path across domains: {path}")
            seen_paths.add(path)
            if not isinstance(record, dict):
                fail(f"{path}: file record must be an object.")
            extra_file = set(record.keys()) - ALLOWED_FILE_KEYS
            if extra_file:
                fail(f"{path}: unexpected file keys: {sorted(extra_file)}")
            defs_list = record.get("defs")
            if not isinstance(defs_list, list):
                fail(f"{path}: defs must be a list.")
            for defn in defs_list:
                if not isinstance(defn, dict):
                    fail(f"{path}: each def must be an object.")
                validate_def(defn, path)
            defs_count = len(defs_list)
            if defs_count == 1:
                domain_single_calc += 1
            elif defs_count > 1:
                domain_multi_calc += 1

        if domain_single_calc != domain_single:
            fail(f"{domain_name}: single must equal computed total ({domain_single_calc}).")
        if domain_multi_calc != domain_multi:
            fail(f"{domain_name}: multi must equal computed total ({domain_multi_calc}).")

        computed_single += domain_single_calc
        computed_multi += domain_multi_calc

    if computed_single != single_total:
        fail(f"single must equal computed total ({computed_single}).")
    if computed_multi != multi_total:
        fail(f"multi must equal computed total ({computed_multi}).")

    print("OK: defs evidence is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
