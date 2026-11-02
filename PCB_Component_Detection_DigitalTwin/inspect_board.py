"""Inspect a PCB: detect components, analyze the circuit, explain it, export the digital twin.

    # Offline demo with saved detections
    python inspect_board.py --detections samples/sample_detections.json

    # Live: YOLO model hosted on Roboflow
    export ROBOFLOW_API_KEY=...
    python inspect_board.py --image board.jpg --model pcb-components --version 3

    # Ask the chatbot a follow-up question (uses ANTHROPIC_API_KEY or OPENAI_API_KEY if set)
    python inspect_board.py --detections samples/sample_detections.json --question "How can I reduce noise?"

Writes output/analysis.json, output/digital_twin.json and output/detections.png.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pcb_inspector import analyze, ask, infer_image, load_detections, to_digital_twin

HERE = Path(__file__).parent


def draw(analysis: dict, out: Path, image: Path | None = None) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.patches as patches
    import matplotlib.pyplot as plt
    from pcb_inspector.twin import STATUS_COLORS

    w, h = analysis["image"]["width"], analysis["image"]["height"]
    fig, ax = plt.subplots(figsize=(10, 10 * h / w))
    if image and image.exists():
        ax.imshow(plt.imread(image))
    else:
        ax.add_patch(patches.Rectangle((0, 0), w, h, color="#1f5130"))  # bare-board background
    for c in analysis["components"]:
        x0, y0 = c["x"] - c["width"] / 2, c["y"] - c["height"] / 2
        color = STATUS_COLORS[c["status"]]
        ax.add_patch(patches.Rectangle((x0, y0), c["width"], c["height"], fill=False, lw=2, edgecolor=color))
        ax.text(x0, y0 - 6, f"{c['ref']} {c['confidence']:.0%}", color="white", fontsize=8,
                bbox={"facecolor": color, "edgecolor": "none", "pad": 1.5})
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    ax.set_title(f"Detected components (green ok, amber review, red issue), score {analysis['quality_score']}/100")
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--image", help="local image path or URL (requires --model and --version)")
    src.add_argument("--detections", type=Path, help="saved Roboflow JSON response")
    parser.add_argument("--model", help="Roboflow model id, e.g. pcb-components")
    parser.add_argument("--version", help="Roboflow model version")
    parser.add_argument("--expected-bom", type=Path, help='JSON like {"resistor": 4, "capacitor": 6}')
    parser.add_argument("--board-width-mm", type=float, default=100.0)
    parser.add_argument("--question", help="question for the circuit chatbot")
    parser.add_argument("--out", type=Path, default=HERE / "output")
    args = parser.parse_args()

    if args.image:
        if not (args.model and args.version):
            parser.error("--image needs --model and --version")
        result = infer_image(args.image, args.model, args.version)
    else:
        result = load_detections(args.detections)

    expected = json.loads(args.expected_bom.read_text()) if args.expected_bom else None
    analysis = analyze(result, expected)
    twin = to_digital_twin(analysis, args.board_width_mm)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "analysis.json").write_text(json.dumps(analysis, indent=2))
    (args.out / "digital_twin.json").write_text(json.dumps(twin, indent=2))
    local_image = Path(args.image) if args.image and not args.image.startswith("http") else None
    draw(analysis, args.out / "detections.png", local_image)

    print(f"BOM: {analysis['bom']}")
    print(f"Quality score: {analysis['quality_score']}/100, findings: {len(analysis['findings'])}\n")
    print(ask(analysis, args.question))
    print(f"\nOutputs written to {args.out}")


if __name__ == "__main__":
    main()
