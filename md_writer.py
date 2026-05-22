"""Write the final Markdown file with Mermaid diagrams and summary tables."""

from pathlib import Path
from pos_parser import Graph, Node


def write_markdown(out_path: Path, graph: Graph, mermaid: str) -> None:
    """Write the complete Markdown output file."""
    lines: list[str] = []

    lines.append(f"# {graph.title}")
    lines.append("")

    # Overview
    node_count = len(graph.nodes)
    edge_count = len(graph.edges)
    pool_count = len(graph.pools)
    lines.append(f"**节点数**: {node_count} | **连线数**: {edge_count} | **泳池数**: {pool_count}")
    lines.append("")

    # Mermaid diagram
    lines.append("## 流程图")
    lines.append("")
    lines.append(mermaid)
    lines.append("")

    # Summary table
    lines.append("## 步骤列表")
    lines.append("")

    if graph.pools:
        for pool in graph.pools:
            lines.append(f"### {pool.text}")
            lines.append("")
            _write_pool_table(lines, pool, graph)
    else:
        _write_simple_table(lines, graph)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_pool_table(lines: list[str], pool, graph: Graph) -> None:
    """Write a table for nodes within a specific pool, grouped by lane."""
    for lane in pool.lanes:
        lane_nodes = [n for n in graph.nodes if n.lane_id == lane.id]
        unassigned = [n for n in graph.nodes if n.pool_id == pool.id and not n.lane_id]

        if lane_nodes:
            lines.append(f"**{lane.text}**")
            lines.append("")
            lines.append("| 序号 | 名称 | 类型 |")
            lines.append("|------|------|------|")
            for i, node in enumerate(sorted(lane_nodes, key=lambda n: n.y), 1):
                lines.append(f"| {i} | {node.text} | {_type_label(node.name)} |")
            lines.append("")

    if unassigned:
        lines.append("**未分配泳道**")
        lines.append("")
        lines.append("| 序号 | 名称 | 类型 |")
        lines.append("|------|------|------|")
        for i, node in enumerate(sorted(unassigned, key=lambda n: n.y), 1):
            lines.append(f"| {i} | {node.text} | {_type_label(node.name)} |")
        lines.append("")


def _write_simple_table(lines: list[str], graph: Graph) -> None:
    """Write a simple table for graphs without pools."""
    lines.append("| 序号 | 名称 | 类型 |")
    lines.append("|------|------|------|")
    for i, node in enumerate(_sort_nodes(graph.nodes), 1):
        lines.append(f"| {i} | {node.text} | {_type_label(node.name)} |")
    lines.append("")


def _type_label(name: str) -> str:
    labels = {
        "start": "开始/结束",
        "rectangle": "处理",
        "diamond": "判断",
        "note": "备注",
        "text": "文本",
        "standardText": "文本",
    }
    return labels.get(name, name)


def _sort_nodes(nodes: list[Node]) -> list[Node]:
    """Sort nodes by pool, lane, y, x."""
    return sorted(nodes, key=lambda n: (n.pool_id or "", n.lane_id or "", n.y, n.x))