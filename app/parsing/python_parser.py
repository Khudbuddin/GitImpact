import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)


def parse_python_file(file_path: str) -> dict:
    """
    Parses a single Python file and extracts:
    - function definitions
    - class definitions
    - imports
    - function calls, tagged with WHICH function they occurred inside
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()

    source_bytes = bytes(source_code, "utf8")
    tree = parser.parse(source_bytes)
    root_node = tree.root_node

    result = {
        "file": file_path,
        "functions": [],
        "classes": [],
        "imports": [],
        "calls": [],
    }

    def get_text(node):
        return source_bytes[node.start_byte:node.end_byte].decode("utf8")

    def walk(node, current_function=None):
        new_scope = current_function

        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                func_name = get_text(name_node)
                result["functions"].append({
                    "name": func_name,
                    "line": node.start_point[0] + 1
                })
                new_scope = func_name  # everything inside this function belongs to this scope

        elif node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                result["classes"].append({
                    "name": get_text(name_node),
                    "line": node.start_point[0] + 1
                })

        elif node.type in ("import_statement", "import_from_statement"):
            result["imports"].append({
                "text": get_text(node),
                "line": node.start_point[0] + 1
            })

        elif node.type == "call":
            func_node = node.child_by_field_name("function")
            if func_node:
                result["calls"].append({
                    "name": get_text(func_node),
                    "line": node.start_point[0] + 1,
                    "in_function": current_function
                })

        for child in node.children:
            walk(child, new_scope)

    walk(root_node)
    return result


def get_function_source(file_path: str, function_name: str) -> str:
    """Returns the exact source code text of a specific function, by name."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()
    source_bytes = bytes(source_code, "utf8")
    tree = parser.parse(source_bytes)
    root_node = tree.root_node

    found = {"text": None}

    def walk(node):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name_text = source_bytes[name_node.start_byte:name_node.end_byte].decode("utf8")
                if name_text == function_name:
                    found["text"] = source_bytes[node.start_byte:node.end_byte].decode("utf8")
                    return
        for child in node.children:
            walk(child)

    walk(root_node)
    return found["text"]

def get_all_function_sources(file_path: str) -> list:
    """Returns the name + source code of every function in a file."""
    parsed = parse_python_file(file_path)
    results = []
    for func in parsed["functions"]:
        source = get_function_source(file_path, func["name"])
        if source:
            results.append({"name": func["name"], "source": source})
    return results

if __name__ == "__main__":
    import json
    test_file = "app/ingestion/cloner.py"
    parsed = parse_python_file(test_file)
    print(json.dumps(parsed, indent=2))