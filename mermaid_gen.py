"""Generate Mermaid flowchart code from the intermediate graph."""

import re

from pos_parser import Graph, Node, Pool


def generate_mermaid(graph: Graph) -> str:
    """Generate a Mermaid flowchart string from the parsed graph."""
    lines: list[str] = []
    lines.append("```mermaid")
    lines.append("flowchart TD")

    node_map: dict[str, Node] = {n.id: n for n in graph.nodes}

    if graph.pools:
        for pool in graph.pools:
            _emit_pool(lines, pool, graph, node_map, indent="")
    else:
        for node in _sort_by_y(graph.nodes):
            shape = _node_shape(node)
            lines.append(f"    {node.mermaid_id}{shape}")

    # Emit all edges at the top level (after all subgraphs close)
    for edge in graph.edges:
        from_n = node_map.get(edge.from_node_id)
        to_n = node_map.get(edge.to_node_id)
        if from_n and to_n:
            label = f"|{edge.label}|" if edge.label else ""
            lines.append(f"    {from_n.mermaid_id} -->{label} {to_n.mermaid_id}")

    lines.append("```")
    return "\n".join(lines)


def _subgraph_id(text: str) -> str:
    """Generate a safe Mermaid subgraph ID from display text.

    Mermaid subgraph IDs must be alphanumeric; full-width punctuation
    (common in Chinese text) causes lexer errors.
    """
    # Replace full-width punctuation with ASCII equivalents or strip
    result = text.replace("：", "_")   # full-width colon
    result = result.replace("（", "_")  # full-width left paren
    result = result.replace("）", "_")  # full-width right paren
    # Strip remaining non-alphanumeric/underscore/hyphen chars
    result = re.sub(r"[^\w\-]", "_", result)
    # Collapse consecutive underscores
    result = re.sub(r"_+", "_", result)
    return result.strip("_")


def _emit_pool(lines: list[str], pool: Pool, graph: Graph, node_map: dict[str, Node], indent: str):
    """Emit a pool as a Mermaid subgraph (outer container)."""
    indent2 = indent + "    "
    safe_id = _subgraph_id(pool.text)
    lines.append(f"{indent}subgraph {safe_id}[\"{_safe_label(pool.text)}\"]")

    for lane in pool.lanes:
        _emit_lane(lines, lane, graph, node_map, indent2)

    # Nodes in this pool but not in any specific lane
    unassigned = [n for n in graph.nodes if n.pool_id == pool.id and not n.lane_id]
    for node in _sort_by_y(unassigned):
        shape = _node_shape(node)
        lines.append(f"{indent2}{node.mermaid_id}{shape}")

    lines.append(f"{indent}end")


def _emit_lane(lines: list[str], lane, graph: Graph, node_map: dict[str, Node], indent: str):
    """Emit a lane as a nested subgraph within a pool."""
    indent2 = indent + "    "
    safe_id = _subgraph_id(lane.text)
    lines.append(f"{indent}subgraph {safe_id}[\"{_safe_label(lane.text)}\"]")

    lane_nodes = [n for n in graph.nodes if n.lane_id == lane.id]
    for node in _sort_by_y(lane_nodes):
        shape = _node_shape(node)
        lines.append(f"{indent2}{node.mermaid_id}{shape}")

    lines.append(f"{indent}end")


def _node_shape(node: Node) -> str:
    """Return the Mermaid shape syntax for a node."""
    label = _safe_label(node.text)
    if node.name == "start":
        return f"([\"{label}\"])"
    elif node.name == "diamond":
        return f"{{\"{label}\"}}"
    else:
        return f"[\"{label}\"]"


def _safe_label(text: str) -> str:
    """Escape double-quotes for Mermaid labels."""
    return text.replace('"', "'")


def _sort_by_y(nodes: list[Node]) -> list[Node]:
    """Sort nodes top-to-bottom (by y-coordinate) to roughly preserve layout."""
    return sorted(nodes, key=lambda n: (n.y, n.x))