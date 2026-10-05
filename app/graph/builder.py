import os
import networkx as nx


def build_dependency_graph(parsed_files: list, parsed_sql_files: list | None = None) -> nx.DiGraph:
    """
    Builds a unified dependency graph from parsed file data.

    Nodes:
      - File nodes (type='file')
      - Function / Method nodes (type='function')
      - Table nodes (type='table', from SQL files)

    Edges:
      - 'contains': File -> Function, or File -> Table
      - 'calls': Function -> Function (enclosed calls)
      - 'imports': File -> File
    """
    graph = nx.DiGraph()

    # Pass 1: Add all file nodes and contained function nodes
    for file_data in parsed_files:
        raw_path = file_data["file"]
        file_path = raw_path.replace("\\", "/")
        graph.add_node(file_path, type="file", label=os.path.basename(file_path))

        function_list = file_data.get("functions", []) + file_data.get("methods", [])
        for func in function_list:
            func_id = f"{file_path}::{func['name']}"
            graph.add_node(func_id, type="function", name=func["name"], line=func.get("line", 1), file=file_path)
            graph.add_edge(file_path, func_id, relation="contains")

    # Pass 1b: Add SQL tables if present
    if parsed_sql_files:
        for sql_data in parsed_sql_files:
            file_path = sql_data["file"].replace("\\", "/")
            graph.add_node(file_path, type="file", label=os.path.basename(file_path))
            for table in sql_data.get("tables", []):
                table_id = f"{file_path}::{table['name']}"
                graph.add_node(table_id, type="table", name=table["name"], columns=table.get("columns", []))
                graph.add_edge(file_path, table_id, relation="contains")

    # Pass 2: Connect function calls ONLY to calls made inside that specific function
    all_function_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "function"]

    for file_data in parsed_files:
        file_path = file_data["file"].replace("\\", "/")
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

    # Pass 3: Connect files based on imports (cross-platform safe basename & path matching)
    file_basenames = {}
    for f in parsed_files:
        clean_path = f["file"].replace("\\", "/")
        base_no_ext = os.path.splitext(os.path.basename(clean_path))[0]
        if base_no_ext:
            file_basenames[base_no_ext] = clean_path

    for file_data in parsed_files:
        file_path = file_data["file"].replace("\\", "/")
        for imp in file_data.get("imports", []):
            import_text = imp.get("text", "")
            for basename, target_file in file_basenames.items():
                if basename != "__init__" and basename in import_text and target_file != file_path:
                    graph.add_edge(file_path, target_file, relation="imports")

    return graph


def get_file_level_view(graph: nx.DiGraph) -> nx.DiGraph:
    """Returns a smaller graph showing ONLY files and their import relationships."""
    file_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "file"]
    subgraph = graph.subgraph(file_nodes).copy()
    edges_to_remove = [(u, v) for u, v, d in subgraph.edges(data=True) if d.get("relation") != "imports"]
    subgraph.remove_edges_from(edges_to_remove)
    return subgraph


def get_function_level_view(graph: nx.DiGraph, file_path: str) -> nx.DiGraph:
    """Returns the functions belonging to one specific file, plus anything they call."""
    clean_path = file_path.replace("\\", "/")
    nodes_to_keep = [n for n in graph.nodes if n == clean_path or n.startswith(f"{clean_path}::")]
    for node in list(nodes_to_keep):
        nodes_to_keep.extend(graph.successors(node))
    return graph.subgraph(set(nodes_to_keep)).copy()


def get_graph_summary(graph: nx.DiGraph) -> dict:
    """Extracts high-level topological insights for architecture answers."""
    file_view = get_file_level_view(graph)
    total_files = len(file_view.nodes)
    total_imports = len(file_view.edges)
    total_functions = len([n for n, d in graph.nodes(data=True) if d.get("type") == "function"])
    total_calls = len([(u, v) for u, v, d in graph.edges(data=True) if d.get("relation") == "calls"])

    # Central hub files: files imported by the highest number of other files (in-degree in import graph)
    in_degrees = dict(file_view.in_degree())
    sorted_hubs = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
    top_hubs = [
        {"file": os.path.basename(node), "path": node, "imported_by_count": deg}
        for node, deg in sorted_hubs[:5] if deg > 0
    ]

    # Entry files: files that import others or have out-edges, but are imported by 0 files
    out_degrees = dict(file_view.out_degree())
    entry_candidates = [
        {"file": os.path.basename(node), "path": node, "out_degree": out_degrees.get(node, 0)}
        for node in file_view.nodes
        if in_degrees.get(node, 0) == 0 and out_degrees.get(node, 0) > 0
    ]

    return {
        "total_files": total_files,
        "total_functions": total_functions,
        "total_imports": total_imports,
        "total_calls": total_calls,
        "top_hubs": top_hubs,
        "entry_points": entry_candidates[:5]
    }


def generate_mermaid_diagram(graph: nx.DiGraph, max_nodes: int = 15) -> str:
    """Generates a Mermaid graph TD diagram of file connections."""
    file_view = get_file_level_view(graph)
    edges = list(file_view.edges)
    if not edges:
        return ""

    mermaid_lines = ["flowchart TD"]
    node_id_map = {}
    counter = 1

    def get_id(path):
        nonlocal counter
        if path not in node_id_map:
            node_id_map[path] = f"N{counter}"
            counter += 1
        return node_id_map[path]

    edges_to_show = edges[:max_nodes]
    for u, v in edges_to_show:
        u_id = get_id(u)
        v_id = get_id(v)
        u_label = os.path.basename(u)
        v_label = os.path.basename(v)
        mermaid_lines.append(f'    {u_id}["{u_label}"] --> {v_id}["{v_label}"]')

    return "\n".join(mermaid_lines)


def generate_function_call_mermaid(graph: nx.DiGraph, max_edges: int = 35) -> str:
    """Generates a Mermaid flowchart TD diagram of function-to-function calls."""
    call_edges = [(u, v) for u, v, d in graph.edges(data=True) if d.get("relation") == "calls"]
    if not call_edges:
        return ""

    mermaid_lines = ["flowchart TD"]
    node_id_map = {}
    counter = 1

    def get_id(func_id):
        nonlocal counter
        if func_id not in node_id_map:
            node_id_map[func_id] = f"F{counter}"
            counter += 1
        return node_id_map[func_id]

    edges_to_show = call_edges[:max_edges]
    for u, v in edges_to_show:
        u_id = get_id(u)
        v_id = get_id(v)
        u_label = os.path.basename(u.split("::")[0]) + "::" + u.split("::")[-1]
        v_label = os.path.basename(v.split("::")[0]) + "::" + v.split("::")[-1]
        mermaid_lines.append(f'    {u_id}["{u_label}"] --> {v_id}["{v_label}"]')

    return "\n".join(mermaid_lines)