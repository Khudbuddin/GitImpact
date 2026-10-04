import networkx as nx


def find_impact(graph: nx.DiGraph, target_node: str) -> dict:
    """
    Performs a reverse BFS traversal to identify all upstream dependents
    (functions or files that call/import the target node).
    """
    clean_target = target_node.replace("\\", "/")
    if clean_target not in graph:
        # Fallback: check if target is an un-prefixed function name
        matching_nodes = [n for n in graph.nodes if n.endswith(f"::{clean_target}") or n.endswith(clean_target)]
        if matching_nodes:
            clean_target = matching_nodes[0]
        else:
            return {"error": f"Node '{target_node}' not found in the dependency graph."}

    def relevant_predecessors(node):
        """Only follow edges that represent real dependency (calls/imports)."""
        preds = []
        for pred in graph.predecessors(node):
            edge_data = graph.get_edge_data(pred, node)
            if edge_data and edge_data.get("relation") in ("calls", "imports"):
                preds.append(pred)
        return preds

    direct_dependents = relevant_predecessors(clean_target)

    all_dependents = {}
    visited = set()
    queue = [(clean_target, 0)]

    while queue:
        current_node, distance = queue.pop(0)
        if current_node in visited:
            continue
        visited.add(current_node)

        for predecessor in relevant_predecessors(current_node):
            if predecessor not in visited:
                all_dependents[predecessor] = distance + 1
                queue.append((predecessor, distance + 1))

    return {
        "target": clean_target,
        "target_type": graph.nodes[clean_target].get("type", "unknown"),
        "direct_dependents": direct_dependents,
        "all_dependents": [
            {"node": node, "distance": dist, "type": graph.nodes[node].get("type", "unknown")}
            for node, dist in sorted(all_dependents.items(), key=lambda x: x[1])
        ],
        "total_affected": len(all_dependents)
    }


def get_file_connections_summary(graph: nx.DiGraph, file_path: str) -> dict:
    """Finds all incoming and outgoing connections for a specific file."""
    clean_file = file_path.replace("\\", "/")
    if clean_file not in graph:
        return {"error": f"File '{file_path}' not found in graph."}

    imported_by = [
        pred for pred in graph.predecessors(clean_file)
        if graph.get_edge_data(pred, clean_file, {}).get("relation") == "imports"
    ]

    imports_files = [
        succ for succ in graph.successors(clean_file)
        if graph.get_edge_data(clean_file, succ, {}).get("relation") == "imports"
    ]

    contained_functions = [
        succ for succ in graph.successors(clean_file)
        if graph.get_edge_data(clean_file, succ, {}).get("relation") == "contains"
    ]

    return {
        "file": clean_file,
        "imported_by": imported_by,
        "imports_files": imports_files,
        "contained_functions": contained_functions
    }