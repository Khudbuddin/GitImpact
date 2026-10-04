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
    - method calls
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()

    source_bytes = bytes(source_code, "utf8")
    tree = parser.parse(source_bytes)
    root_node = tree.root_node

    result = {
        "file": file_path,
        "methods": [],
        "classes": [],
        "imports": [],
        "calls": [],
    }

    def get_text(node):
        return source_bytes[node.start_byte:node.end_byte].decode("utf8")

    def walk(node):
        # Method definitions
        if node.type == "method_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                result["methods"].append({
                    "name": get_text(name_node),
                    "line": node.start_point[0] + 1
                })

        # Class definitions
        elif node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                result["classes"].append({
                    "name": get_text(name_node),
                    "line": node.start_point[0] + 1
                })

        # Imports
        elif node.type == "import_declaration":
            result["imports"].append({
                "text": get_text(node),
                "line": node.start_point[0] + 1
            })

        # Method calls
        elif node.type == "method_invocation":
            name_node = node.child_by_field_name("name")
            if name_node:
                result["calls"].append({
                    "name": get_text(name_node),
                    "line": node.start_point[0] + 1
                })

        for child in node.children:
            walk(child)

    walk(root_node)
    return result


if __name__ == "__main__":
    import json
    # You'll need a sample .java file to test with — create one manually for now
    test_file = "data/sample.java"
    parsed = parse_java_file(test_file)
    print(json.dumps(parsed, indent=2))