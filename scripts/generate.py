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


def get_parser(language: str):
    try:
        from tree_sitter_languages import get_parser as ts_get_parser
    except Exception as e:
        fail(f"tree_sitter_languages is required: {e}")
    try:
        return ts_get_parser(language)
    except Exception as e:
        fail(f"Unsupported language '{language}': {e}")

def language_for_path(path: str) -> str | None:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".py":
        return "python"
    if ext in (".js", ".mjs", ".cjs", ".jsx"):
        return "javascript"
    if ext in (".ts", ".tsx"):
        return "typescript"
    if ext == ".go":
        return "go"
    if ext == ".java":
        return "java"
    if ext == ".rs":
        return "rust"
    if ext in (".c", ".h"):
        return "c"
    if ext in (".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx"):
        return "cpp"
    return None

def node_text(content_bytes: bytes, node) -> str:
    return content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

def find_named_child(node, types: List[str]):
    for child in node.named_children:
        if child.type in types:
            return child
    return None

def extract_name(node, content_bytes: bytes) -> str:
    name_node = node.child_by_field_name("name")
    if name_node is None:
        name_node = find_named_child(node, ["identifier", "type_identifier"])
    if name_node is None:
        return ""
    return node_text(content_bytes, name_node).strip()

def add_def(defs_list: List[Dict], kind: str, node, content_bytes: bytes) -> None:
    name = extract_name(node, content_bytes)
    if not name:
        return
    lineno = node.start_point[0] + 1
    defs_list.append({"kind": kind, "name": name, "lineno": lineno})

def extract_top_level_defs(language: str, root, content_bytes: bytes) -> List[Dict]:
    defs_list: List[Dict] = []

    def handle_node(node):
        ntype = node.type
        if language == "python":
            if ntype == "function_definition":
                add_def(defs_list, "function", node, content_bytes)
                return
            if ntype == "class_definition":
                add_def(defs_list, "class", node, content_bytes)
                return
        if language in ("javascript", "typescript"):
            if ntype == "function_declaration":
                add_def(defs_list, "function", node, content_bytes)
                return
            if ntype == "class_declaration":
                add_def(defs_list, "class", node, content_bytes)
                return
        if language == "go":
            if ntype in ("function_declaration", "method_declaration"):
                add_def(defs_list, "function", node, content_bytes)
                return
            if ntype == "type_declaration":
                for child in node.named_children:
                    if child.type == "type_spec":
                        add_def(defs_list, "class", child, content_bytes)
                return
        if language == "java":
            if ntype == "method_declaration":
                add_def(defs_list, "function", node, content_bytes)
                return
            if ntype in ("class_declaration", "interface_declaration", "record_declaration", "enum_declaration"):
                add_def(defs_list, "class", node, content_bytes)
                return
        if language == "rust":
            if ntype == "function_item":
                add_def(defs_list, "function", node, content_bytes)
                return
            if ntype in ("struct_item", "enum_item", "trait_item", "impl_item"):
                add_def(defs_list, "class", node, content_bytes)
                return
        if language in ("c", "cpp"):
            if ntype == "function_definition":
                add_def(defs_list, "function", node, content_bytes)
                return
            if ntype in ("struct_specifier", "class_specifier", "enum_specifier"):
                add_def(defs_list, "class", node, content_bytes)
                return

    for child in root.named_children:
        if child.type == "export_statement":
            exported = find_named_child(child, ["function_declaration", "class_declaration"])
            if exported is not None:
                handle_node(exported)
                continue
        handle_node(child)
        if language in ("c", "cpp") and child.type == "declaration":
            for sub in child.named_children:
                handle_node(sub)

    defs_list.sort(key=lambda x: (x["lineno"], x["kind"], x["name"]))
    return defs_list

def analyze_file(path: str) -> List[Dict]:
    try:
        content_bytes = open(path, "rb").read()
    except Exception as e:
        fail(f"Failed to read {path}: {e}")

    language = language_for_path(path)
    if not language:
        return []

    parser = get_parser(language)
    tree = parser.parse(content_bytes)
    return extract_top_level_defs(language, tree.root_node, content_bytes)


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
