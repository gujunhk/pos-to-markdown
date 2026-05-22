# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Convert **ProcessOn** (`.pos`) diagram files into Markdown with Mermaid flowcharts. ProcessOn is a Chinese online diagramming tool (processon.com); `.pos` files are JSON exports containing flowchart/swimlane/connector elements.

## Input / Output

- Place `.pos` files in [`input/`](input/)
- Run `python main.py` to process all `.pos` files
- Generated `.md` files go to [`output/`](output/)

## Architecture

4-module pipeline, each step a single file:

1. **[`main.py`](main.py)** — CLI entry point: discovers `.pos` files in `input/`, orchestrates the pipeline, writes output
2. **[`pos_parser.py`](pos_parser.py)** — Parses `.pos` JSON into a `Graph` dataclass. Key decisions:
   - `verticalPool` → `Pool` with child `Lane` objects
   - `verticalLane` → `Lane`; nodes assigned to lanes by matching x-coordinate against lane boundaries
   - `rectangle`/`diamond`/`start`/`note`/`text`/`standardText` → `Node` (text extracted from `textBlock`, HTML tags stripped)
   - `linker` → `Edge` with `from.id`/`to.id`; only edges between known nodes are kept
3. **[`mermaid_gen.py`](mermaid_gen.py)** — Generates Mermaid `flowchart TD` syntax from the `Graph`
   - Shape mapping: `start` → `([text])`, `diamond` → `{text}`, others → `[text]`
   - Pools/lanes → nested `subgraph` blocks
   - All edges emitted at the end (after subgraphs close) to handle cross-lane connections
4. **[`md_writer.py`](md_writer.py)** — Writes the final Markdown: title + stats + Mermaid code block + per-pool tables (node number, name, type)

## .pos File Format (key element types)

The `.pos` file is JSON with `{"diagram": {"elements": {"elements": {...}}}}`.

| `name` | Role | Key fields |
|---|---|---|
| `verticalPool` | Top-level swimlane container | `children` (list of lane IDs), `props.{x,y,w,h}`, `textBlock` |
| `verticalLane` | Swimlane column | `parent` (pool ID), `props.{x,y,w,h}`, `textBlock` |
| `rectangle` | Process step | `container` (pool ID), `textBlock`, `props.{x,y}` |
| `diamond` | Decision/branch | same as rectangle |
| `start` | Terminal (start/end) | same as rectangle |
| `note` | Annotation | same as rectangle |
| `linker` | Connector/edge | `from.id`, `to.id`, `textBlock` (edge label) |

- Text is in `textBlock[].text`; may contain `<div>`, `<br>` HTML tags
- Nodes reference pools via `container` field; lane assignment is done by x-coordinate matching
- Linker labels often contain Chinese branch labels (是/否)

## No External Dependencies

Uses only Python 3 stdlib (`json`, `re`, `dataclasses`, `pathlib`). No `requirements.txt` needed.