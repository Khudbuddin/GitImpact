import networkx as nx

def find_impact(graph: nx.DiGraph, target_node: str) -> dict:
    if target_node not in graph:
        return {"error": f"Node '{target_node}' not found in the graph."}

    def relevant_predecessors(node):
        """Only follow edges that represent real dependency (calls/imports),
        not structural containment (a file containing a function)."""
        preds = []
        for pred in graph.predecessors(node):
            edge_data = graph.get_edge_data(pred, node)
            if edge_data.get("relation") in ("calls", "imports"):
                preds.append(pred)
        return preds

    direct_dependents = relevant_predecessors(target_node)

    all_dependents = {}
    visited = set()
    queue = [(target_node, 0)]

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
        "target": target_node,
        "target_type": graph.nodes[target_node].get("type"),
        "direct_dependents": direct_dependents,
        "all_dependents": [
            {"node": node, "distance": dist, "type": graph.nodes[node].get("type")}
            for node, dist in sorted(all_dependents.items(), key=lambda x: x[1])
        ],
        "total_affected": len(all_dependents)
    }


if __name__ == "__main__":
    from app.parsing.python_parser import parse_python_file
    from app.graph.builder import build_dependency_graph

    files_to_test = ["app/ingestion/cloner.py", "app/parsing/python_parser.py"]
    parsed_data = [parse_python_file(f) for f in files_to_test]
    g = build_dependency_graph(parsed_data)

    # Test: what breaks if we change get_text?
    target = "app/parsing/python_parser.py::get_text"
    result = find_impact(g, target)

    import json
    print(json.dumps(result, indent=2))