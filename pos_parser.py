"""Parse ProcessOn .pos JSON files into an intermediate graph representation."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Node:
    id: str
    name: str  # element type: rectangle, diamond, start, note, text, etc.
    text: str  # human-readable label (from textBlock)
    pool_id: str = ""
    lane_id: str = ""
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0

    @property
    def mermaid_id(self) -> str:
        return f"n_{_sanitize_id(self.id)}"


@dataclass
class Edge:
    id: str
    from_node_id: str
    to_node_id: str
    label: str = ""


@dataclass
class Lane:
    id: str
    text: str
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0


@dataclass
class Pool:
    id: str
    text: str
    lanes: list[Lane] = field(default_factory=list)
    x: float = 0
    y: float = 0
    w: float = 0
    h: float = 0


@dataclass
class Graph:
    title: str
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    pools: list[Pool] = field(default_factory=list)


def _sanitize_id(raw_id: str) -> str:
    """Make a ProcessOn element ID safe for Mermaid node identifiers."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", raw_id)


def _extract_text(text_block: list[dict]) -> str:
    """Extract text from a ProcessOn textBlock, cleaning HTML tags."""
    if not text_block:
        return ""
    parts = []
    for tb in text_block:
        t = tb.get("text", "")
        t = re.sub(r"<br\s*/?>", " / ", t)
        t = re.sub(r"<[^>]+>", "", t)
        parts.append(t)
    return " / ".join(p for p in parts if p)


def parse_pos(filepath: Path) -> Graph:
    """Parse a .pos file and return a Graph."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    diagram = data.get("diagram", data)
    elements = diagram.get("elements", {})
    elem_map = elements.get("elements", {})

    graph = Graph(title=filepath.stem)

    # First pass: collect pools and lanes
    pools: dict[str, Pool] = {}
    lanes_by_pool: dict[str, list[Lane]] = {}

    for eid, e in elem_map.items():
        ename = e.get("name", "")
        props = e.get("props", {})
        tb = e.get("textBlock", [])

        if ename == "verticalPool":
            pool = Pool(
                id=eid,
                text=_extract_text(tb),
                x=props.get("x", 0),
                y=props.get("y", 0),
                w=props.get("w", 0),
                h=props.get("h", 0),
            )
            pools[eid] = pool
            lanes_by_pool.setdefault(eid, [])

        elif ename == "verticalLane":
            parent = e.get("parent", "")
            lane = Lane(
                id=eid,
                text=_extract_text(tb),
                x=props.get("x", 0),
                y=props.get("y", 0),
                w=props.get("w", 0),
                h=props.get("h", 0),
            )
            lanes_by_pool.setdefault(parent, []).append(lane)

    # Assign lanes to pools (sorted by x position)
    for pool_id, lanes in lanes_by_pool.items():
        if pool_id in pools:
            pools[pool_id].lanes = sorted(lanes, key=lambda l: l.x)

    # Second pass: collect nodes (non-linker, non-pool, non-lane)
    shape_types = {"rectangle", "diamond", "start", "note", "text", "standardText"}
    nodes: dict[str, Node] = {}

    for eid, e in elem_map.items():
        ename = e.get("name", "")
        if ename not in shape_types:
            continue

        props = e.get("props", {})
        tb = e.get("textBlock", [])
        text = _extract_text(tb)
        container = e.get("container", "")

        node = Node(
            id=eid,
            name=ename,
            text=text,
            pool_id=container,
            x=props.get("x", 0),
            y=props.get("y", 0),
            w=props.get("w", 0),
            h=props.get("h", 0),
        )

        # Determine which lane this node belongs to
        if container in pools:
            pool = pools[container]
            for lane in pool.lanes:
                # Check if node's x falls within this lane's horizontal span
                if lane.x <= node.x < lane.x + lane.w:
                    node.lane_id = lane.id
                    break

        nodes[eid] = node

    # Third pass: collect edges (linkers) between known nodes
    edges: list[Edge] = []
    for eid, e in elem_map.items():
        if e.get("name") != "linker":
            continue

        from_id = e.get("from", {}).get("id", "")
        to_id = e.get("to", {}).get("id", "")

        if from_id in nodes and to_id in nodes:
            label = _extract_text(e.get("textBlock", []))
            if not label:
                label = e.get("text", "")
            edges.append(Edge(id=eid, from_node_id=from_id, to_node_id=to_id, label=label))

    graph.nodes = list(nodes.values())
    graph.edges = edges
    graph.pools = [pools[pid] for pid in pools]

    return graph