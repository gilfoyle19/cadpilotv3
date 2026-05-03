from __future__ import annotations

import argparse
from pathlib import Path

from langchain_core.runnables.graph import MermaidDrawMethod

from cadpilotv3.config.settings import get_settings
from cadpilotv3.graph.pipeline import build_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the CadPilot LangGraph pipeline to a PNG file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="artifacts/pipeline_graph.png",
        help="PNG output path. Defaults to artifacts/pipeline_graph.png.",
    )
    parser.add_argument(
        "--method",
        choices=("api", "pyppeteer"),
        default="api",
        help=(
            "Mermaid render method. 'api' uses the Mermaid image service; "
            "'pyppeteer' renders locally if pyppeteer/browser deps are installed."
        ),
    )
    parser.add_argument(
        "--mermaid",
        default=None,
        help="Optional path to also write the Mermaid diagram source.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    settings = get_settings()
    pipeline = build_pipeline(settings)
    graph = pipeline.get_graph()

    if args.mermaid:
        mermaid_path = Path(args.mermaid)
        mermaid_path.parent.mkdir(parents=True, exist_ok=True)
        mermaid_path.write_text(graph.draw_mermaid(), encoding="utf-8")

    draw_method = MermaidDrawMethod.API
    if args.method == "pyppeteer":
        draw_method = MermaidDrawMethod.PYPPETEER

    graph.draw_mermaid_png(
        output_file_path=str(output_path),
        draw_method=draw_method,
        background_color="white",
        padding=20,
    )

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
