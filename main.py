"""Convert ProcessOn .pos files to Markdown with Mermaid diagrams."""

import sys
from pathlib import Path
from pos_parser import parse_pos
from mermaid_gen import generate_mermaid
from md_writer import write_markdown


def main():
    input_dir = Path("input")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    pos_files = list(input_dir.glob("*.pos"))
    if not pos_files:
        print("No .pos files found in input/")
        sys.exit(1)

    for pos_file in pos_files:
        print(f"Processing: {pos_file.name}")
        graph = parse_pos(pos_file)
        mermaid = generate_mermaid(graph)
        out_path = output_dir / f"{pos_file.stem}.md"
        write_markdown(out_path, graph, mermaid)
        print(f"  -> {out_path.name}")

    print("Done.")


if __name__ == "__main__":
    main()