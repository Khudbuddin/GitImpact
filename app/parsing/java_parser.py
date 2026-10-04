import tree_sitter_java as tsjava
from tree_sitter import Language, Parser

JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser(JAVA_LANGUAGE)


def parse_java_file(file_path: str) -> dict:
    """
    Parses a single Java file and extracts:
    - method definitions
    - class definitions
    - imports
    - method calls (tagged with enclosing method scope)
    """
    norm_path = file_path.replace("\\", "/")
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()

    source_bytes = bytes(source_code, "utf8")
    tree = parser.parse(source_bytes)
    root_node = tree.root_node

    result = {
        "file": norm_path,
        "methods": [],
        "functions": [],  # alias for unified graph builder
        "classes": [],
        "imports": [],
        "calls": [],
    }

    def get_text(node):
        return source_bytes[node.start_byte:node.end_byte].decode("utf8")

    def walk(node, current_method=None):
        new_scope = current_method

        # Method or constructor definitions
        if node.type in ("method_declaration", "constructor_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                method_name = get_text(name_node)
                method_entry = {
                    "name": method_name,
                    "line": node.start_point[0] + 1
                }
                result["methods"].append(method_entry)
                result["functions"].append(method_entry)
                new_scope = method_name

        # Class or interface definitions
        elif node.type in ("class_declaration", "interface_declaration", "enum_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                result["classes"].append({
                    "name": get_text(name_node),
                    "line": node.start_point[0] + 1
                })

        # Imports
        elif node.type == "import_declaration":
            result["imports"].append({
                "text": get_text(node).strip(),
                "line": node.start_point[0] + 1
            })

        # Method calls
        elif node.type == "method_invocation":
            name_node = node.child_by_field_name("name")
            if name_node:
                result["calls"].append({
                    "name": get_text(name_node),
                    "line": node.start_point[0] + 1,
                    "in_function": current_method
                })

        for child in node.children:
            walk(child, new_scope)

    walk(root_node)
    return result


def get_java_method_source(file_path: str, method_name: str) -> str | None:
    """Returns the exact source code of a specific Java method by name."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()

    source_bytes = bytes(source_code, "utf8")
    tree = parser.parse(source_bytes)
    root_node = tree.root_node

    found = {"text": None}

    def walk(node):
        if node.type in ("method_declaration", "constructor_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                name_text = source_bytes[name_node.start_byte:name_node.end_byte].decode("utf8")
                if name_text == method_name:
                    found["text"] = source_bytes[node.start_byte:node.end_byte].decode("utf8")
                    return
        for child in node.children:
            walk(child)

    walk(root_node)
    return found["text"]


def get_all_java_method_sources(file_path: str) -> list:
    """Returns name and source code of all methods in a Java file."""
    parsed = parse_java_file(file_path)
    results = []
    for method in parsed["methods"]:
        src = get_java_method_source(file_path, method["name"])
        if src:
            results.append({"name": method["name"], "source": src})
    return results


if __name__ == "__main__":
    import json
    test_file = "data/sample.java"
    parsed = parse_java_file(test_file)
    print(json.dumps(parsed, indent=2))