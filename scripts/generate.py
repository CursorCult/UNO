#!/usr/bin/env python3
"""Generate UNO defs evidence using tree-sitter."""

import argparse
import json
import os
import sys
from glob import glob
from typing import Dict, List, Optional


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


EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".java": "java",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",
}

FUNC_NODES = {
    "python": {"function_definition"},
    "javascript": {"function_declaration"},
    "typescript": {"function_declaration"},
    "go": {"function_declaration", "method_declaration"},
    "java": set(),
    "rust": {"function_item"},
    "c": {"function_definition"},
    "cpp": {"function_definition"},
}

CLASS_NODES = {
    "python": {"class_definition"},
    "javascript": {"class_declaration"},
    "typescript": {"class_declaration"},
    "go": set(),
    "java": {"class_declaration", "interface_declaration", "record_declaration", "enum_declaration"},
    "rust": {"struct_item", "enum_item", "trait_item"},
    "c": {"struct_specifier", "enum_specifier"},
    "cpp": {"struct_specifier", "class_specifier", "enum_specifier"},
}

WRAPPER_NODES = {
    "python": {"decorated_definition"},
    "javascript": {"export_statement", "export_default_declaration"},
    "typescript": {"export_statement", "export_default_declaration"},
}


def get_parser(language: str):
    try:
        import tree_sitter_languages as tsl
    except Exception as e:
        fail(f"tree-sitter-languages is required: {e}")
    last_error = None
    if hasattr(tsl, "get_parser"):
        try:
            return tsl.get_parser(language)
        except Exception as e:
            last_error = e
    if hasattr(tsl, "get_language"):
        try:
            from tree_sitter import Parser
            parser = Parser()
            lang = tsl.get_language(language)
            if hasattr(parser, "set_language"):
                parser.set_language(lang)
            else:
                parser.language = lang
            return parser
        except Exception as e:
            last_error = e
    fail(f"Unsupported language '{language}': {last_error}")

def language_for_path(path: str) -> Optional[str]:
    ext = os.path.splitext(path)[1].lower()
    return EXT_TO_LANG.get(ext)

def node_text(content_bytes: bytes, node) -> str:
    return content_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

def find_named_child(node, types: List[str]):
    for child in node.named_children:
        if child.type in types:
            return child
    return None

def find_named_descendant(node, types: List[str]):
    for child in node.named_children:
        if child.type in types:
            return child
        descendant = find_named_descendant(child, types)
        if descendant is not None:
            return descendant
    return None

def extract_name(node, content_bytes: bytes) -> str:
    name_node = node.child_by_field_name("name")
    if name_node is None:
        name_node = find_named_child(node, ["identifier", "type_identifier"])
    if name_node is None and node.type == "function_definition":
        declarator = node.child_by_field_name("declarator")
        if declarator is None:
            declarator = find_named_child(node, ["declarator", "function_declarator"])
        if declarator is not None:
            name_node = find_named_descendant(declarator, ["identifier"])
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
    func_nodes = FUNC_NODES.get(language, set())
    class_nodes = CLASS_NODES.get(language, set())
    wrapper_nodes = WRAPPER_NODES.get(language, set())

    def handle_node(node):
        ntype = node.type
        if ntype in func_nodes:
            add_def(defs_list, "function", node, content_bytes)
            return
        if ntype in class_nodes:
            add_def(defs_list, "class", node, content_bytes)
            return
        if ntype in wrapper_nodes:
            exported = find_named_child(node, list(func_nodes | class_nodes))
            if exported is not None:
                handle_node(exported)
            return
        if language == "go" and ntype == "type_declaration":
            for child in node.named_children:
                if child.type == "type_spec":
                    add_def(defs_list, "class", child, content_bytes)

    for child in root.named_children:
        handle_node(child)
        if language in ("c", "cpp") and child.type in ("declaration", "type_definition"):
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
    parser = argparse.ArgumentParser(description="Generate UNO defs evidence using tree-sitter.")
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
