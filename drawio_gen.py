"""Generate draw.io (diagrams.net) XML from the intermediate graph."""

import time
from xml.sax.saxutils import escape

_QUOTE_ENTITIES = {'"': "&quot;"}

def _xml_escape(text: str) -> str:
    """Escape text safe for double-quoted XML attributes."""
    return escape(text, _QUOTE_ENTITIES)

from pos_parser import Graph, Node, Pool


def _style_for_node(node: Node) -> str:
    """Return a draw.io style string for a given node shape."""
    base = "whiteSpace=wrap;html=1;"
    if node.name == "start":
        return base + "rounded=1;fillColor=#CAEDB4;strokeColor=#5A9E3E;"
    elif node.name == "diamond":
        return base + "rhombus;fillColor=#F5F5F5;strokeColor=#666666;"
    elif node.name == "note":
        return base + "shape=note;backgroundOutline=1;darkOpacity=0.05;fillColor=#FFF2CC;strokeColor=#D6B656;"
    else:
        return base + "rounded=0;fillColor=#DAE8FC;strokeColor=#6C8EBF;"


def _style_for_pool() -> str:
    return "swimlane;whiteSpace=wrap;html=1;fillColor=#E1D5E7;strokeColor=#9673A6;startSize=40;"


def _style_for_lane() -> str:
    return "swimlane;whiteSpace=wrap;html=1;fillColor=#FFE6CC;strokeColor=#D79B00;startSize=30;"


def _style_for_edge() -> str:
    return (
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;"
        "jettySize=auto;html=1;endArrow=classic;endFill=1;"
    )


def generate_drawio(graph: Graph) -> str:
    """Generate a draw.io XML string from the parsed graph."""

    node_map: dict[str, Node] = {n.id: n for n in graph.nodes}

    # Build lane lookup: lane_id -> (lane, pool)
    lane_info: dict[str, tuple] = {}
    for pool in graph.pools:
        for lane in pool.lanes:
            lane_info[lane.id] = (lane, pool)

    parts: list[str] = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(
        '<mxfile host="pos-to-markdown" modified="'
        + time.strftime("%Y-%m-%dT%H:%M:%S")
        + '" agent="pos-to-markdown" version="21.0.0">'
    )
    parts.append(f'  <diagram id="diagram-1" name="{_xml_escape(graph.title)}">')
    parts.append('    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" '
                 'guides="1" tooltips="1" connect="1" arrows="1" '
                 'fold="1" page="1" pageScale="1" '
                 'pageWidth="1600" pageHeight="1200" math="0" shadow="0">')
    parts.append("      <root>")
    parts.append('        <mxCell id="0" />')
    parts.append('        <mxCell id="1" parent="0" />')

    # --- Emit pools as top-level swimlanes ---
    for pool in graph.pools:
        _emit_pool(parts, pool, graph, node_map, lane_info)

    # --- Emit nodes without a pool ---
    for node in graph.nodes:
        if not node.pool_id:
            _emit_node(parts, node, parent="1")

    # --- Emit edges ---
    for edge in graph.edges:
        from_n = node_map.get(edge.from_node_id)
        to_n = node_map.get(edge.to_node_id)
        if from_n and to_n:
            _emit_edge(parts, edge, node_map)

    parts.append("      </root>")
    parts.append("    </mxGraphModel>")
    parts.append("  </diagram>")
    parts.append("</mxfile>")

    return "\n".join(parts)


def _emit_pool(
    parts: list[str],
    pool: Pool,
    graph: Graph,
    node_map: dict[str, Node],
    lane_info: dict[str, tuple],
) -> None:
    """Emit a pool as a draw.io swimlane."""
    pool_id = _safe_id(pool.id)
    style = _style_for_pool()
    value = _xml_escape(pool.text)
    parts.append(
        f'        <mxCell id="{pool_id}" value="{value}" '
        f'style="{style}" vertex="1" parent="1">'
    )
    parts.append(
        f'          <mxGeometry x="{pool.x:.0f}" y="{pool.y:.0f}" '
        f'width="{pool.w:.0f}" height="{pool.h:.0f}" as="geometry" />'
    )
    parts.append(f"        </mxCell>")

    # Lanes (child swimlanes inside this pool)
    for lane in pool.lanes:
        _emit_lane(parts, lane, pool, graph, node_map)

    # Nodes directly in this pool (no lane assignment)
    unassigned = [n for n in graph.nodes if n.pool_id == pool.id and not n.lane_id]
    for node in unassigned:
        _emit_node(parts, node, parent=_safe_id(pool.id),
                   ref_x=pool.x, ref_y=pool.y)


def _emit_lane(
    parts: list[str],
    lane,
    pool: Pool,
    graph: Graph,
    node_map: dict[str, Node],
) -> None:
    """Emit a lane as a nested swimlane within a pool."""
    lane_id = _safe_id(lane.id)
    style = _style_for_lane()
    value = _xml_escape(lane.text)
    # Coordinates relative to pool
    rel_x = lane.x - pool.x
    rel_y = lane.y - pool.y
    parts.append(
        f'        <mxCell id="{lane_id}" value="{value}" '
        f'style="{style}" vertex="1" parent="{_safe_id(pool.id)}">'
    )
    parts.append(
        f'          <mxGeometry x="{rel_x:.0f}" y="{rel_y:.0f}" '
        f'width="{lane.w:.0f}" height="{lane.h:.0f}" as="geometry" />'
    )
    parts.append(f"        </mxCell>")

    # Nodes belonging to this lane
    lane_nodes = [n for n in graph.nodes if n.lane_id == lane.id]
    for node in _sort_by_y(lane_nodes):
        _emit_node(parts, node, parent=lane_id, ref_x=lane.x, ref_y=lane.y)


def _emit_node(parts: list[str], node: Node, parent: str,
               ref_x: float = 0, ref_y: float = 0) -> None:
    """Emit a single node as a draw.io vertex.

    Coordinates are converted to be relative to the parent container
    (ref_x, ref_y). For root-level nodes ref_x/ref_y should be 0.
    """
    nid = _safe_id(node.id)
    style = _style_for_node(node)
    value = _xml_escape(node.text)
    rel_x = node.x - ref_x
    rel_y = node.y - ref_y
    w = node.w if node.w > 0 else 120
    h = node.h if node.h > 0 else 60
    parts.append(
        f'        <mxCell id="{nid}" value="{value}" '
        f'style="{style}" vertex="1" parent="{parent}">'
    )
    parts.append(
        f'          <mxGeometry x="{rel_x:.0f}" y="{rel_y:.0f}" '
        f'width="{w:.0f}" height="{h:.0f}" as="geometry" />'
    )
    parts.append(f"        </mxCell>")


def _emit_edge(
    parts: list[str],
    edge,
    node_map: dict[str, Node],
) -> None:
    """Emit an edge (connector) between two nodes."""
    eid = _safe_id(edge.id)
    style = _style_for_edge()
    value = _xml_escape(edge.label)
    parts.append(
        f'        <mxCell id="{eid}" value="{value}" '
        f'style="{style}" edge="1" parent="1" '
        f'source="{_safe_id(edge.from_node_id)}" '
        f'target="{_safe_id(edge.to_node_id)}">'
    )
    parts.append('          <mxGeometry relative="1" as="geometry" />')
    parts.append(f"        </mxCell>")


def _safe_id(raw_id: str) -> str:
    """Make an element ID safe for XML id attributes.

    XML ids cannot start with a digit or contain certain characters.
    """
    if not raw_id:
        return "unknown"
    safe = raw_id
    if safe[0].isdigit():
        safe = "_" + safe
    return safe


def _sort_by_y(nodes: list[Node]) -> list[Node]:
    """Sort nodes top-to-bottom."""
    return sorted(nodes, key=lambda n: (n.y, n.x))