import networkx as nx


def build_dependency_graph(parsed_files: list) -> nx.DiGraph:
    """
    Builds one unified dependency graph from parsed file data.

    Each file becomes a node (type='file').
    Each function/method inside it becomes a node (type='function'),
    connected to its file with a 'contains' edge.
    Function calls become 'calls' edges between function nodes,
    ONLY when the call actually happened inside that specific function's body.
    Imports become 'imports' edges between file nodes.

    Args:
        parsed_files: list of dicts, each one being the output of
                      parse_python_file() or parse_java_file()

    Returns:
        A networkx DiGraph representing the whole codebase.
    """
    graph = nx.DiGraph()

    # First pass: add every file and every function/method as nodes
    for file_data in parsed_files:
        file_path = file_data["file"]
        graph.add_node(file_path, type="file")

        function_list = file_data.get("functions", []) + file_data.get("methods", [])

        for func in function_list:
            func_id = f"{file_path}::{func['name']}"
            graph.add_node(func_id, type="function", name=func["name"], line=func["line"])
            graph.add_edge(file_path, func_id, relation="contains")

    # Second pass: connect function calls ONLY to calls made inside that specific function
    all_function_nodes = [n for n, d in graph.nodes(data=True) if d["type"] == "function"]

    for file_data in parsed_files:
        file_path = file_data["file"]
        function_list = file_data.get("functions", []) + file_data.get("methods", [])

        for func in function_list:
            caller_id = f"{file_path}::{func['name']}"
            for call in file_data.get("calls", []):
                # Skip any call that didn't happen inside THIS function
                if call.get("in_function") != func["name"]:
                    continue

                call_name = call["name"].split(".")[-1]  # handle obj.method() style calls
                for target_node in all_function_nodes:
                    target_name = graph.nodes[target_node]["name"]
                    if target_name == call_name and target_node != caller_id:
                        graph.add_edge(caller_id, target_node, relation="calls")

    # Third pass: connect files based on imports (best-effort name matching)
    file_basenames = {f["file"].split("/")[-1].replace(".py", "").replace(".java", ""): f["file"]
                       for f in parsed_files}

    for file_data in parsed_files:
        file_path = file_data["file"]
        for imp in file_data.get("imports", []):
            import_text = imp["text"]
            for basename, target_file in file_basenames.items():
                if basename in import_text and target_file != file_path:
                    graph.add_edge(file_path, target_file, relation="imports")

    return graph


def get_file_level_view(graph: nx.DiGraph) -> nx.DiGraph:
    """Returns a smaller graph showing ONLY files and their import relationships —
    used when the user hasn't asked to go deep into function-level detail."""
    file_nodes = [n for n, d in graph.nodes(data=True) if d["type"] == "file"]
    subgraph = graph.subgraph(file_nodes).copy()
    edges_to_remove = [(u, v) for u, v, d in subgraph.edges(data=True) if d.get("relation") != "imports"]
    subgraph.remove_edges_from(edges_to_remove)
    return subgraph


def get_function_level_view(graph: nx.DiGraph, file_path: str) -> nx.DiGraph:
    """Returns the functions belonging to one specific file, plus anything they call —
    used when the user asks to drill down into a specific file."""
    nodes_to_keep = [n for n in graph.nodes if n == file_path or n.startswith(f"{file_path}::")]
    for node in list(nodes_to_keep):
        nodes_to_keep.extend(graph.successors(node))
    return graph.subgraph(set(nodes_to_keep)).copy()


if __name__ == "__main__":
    from app.parsing.python_parser import parse_python_file

    files_to_test = ["app/ingestion/cloner.py", "app/parsing/python_parser.py"]
    parsed_data = [parse_python_file(f) for f in files_to_test]

    g = build_dependency_graph(parsed_data)

    print("All nodes:", list(g.nodes(data=True)))
    print("\nAll edges:", list(g.edges(data=True)))

    print("\n--- File-level view only ---")
    file_view = get_file_level_view(g)
    print("Nodes:", list(file_view.nodes))
    print("Edges:", list(file_view.edges))