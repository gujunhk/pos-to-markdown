"""Convert ProcessOn .pos files to Markdown (Mermaid) and draw.io diagrams."""

import sys
from pathlib import Path
from pos_parser import parse_pos
from mermaid_gen import generate_mermaid
from md_writer import write_markdown
from drawio_gen import generate_drawio


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

        # Markdown + Mermaid
        mermaid = generate_mermaid(graph)
        md_path = output_dir / f"{pos_file.stem}.md"
        write_markdown(md_path, graph, mermaid)
        print(f"  -> {md_path.name}")

        # draw.io
        drawio = generate_drawio(graph)
        drawio_path = output_dir / f"{pos_file.stem}.drawio"
        with open(drawio_path, "w", encoding="utf-8") as f:
            f.write(drawio)
        print(f"  -> {drawio_path.name}")

    print("Done.")


if __name__ == "__main__":
    main()