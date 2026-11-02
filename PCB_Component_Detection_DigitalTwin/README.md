# AI PCB Component Detection, Circuit Chatbot & Digital Twin

An automated inspection pipeline for electronic boards: a **YOLO** model hosted on **Roboflow** detects the components, a circuit analysis builds the bill of materials and runs design checks, an **LLM chatbot** explains the circuit and suggests optimizations, and a **Unity digital twin** rebuilds the board in 3D. The whole flow is orchestrated by **n8n** workflows.



## Architecture

```
board photo
   │
   ▼
n8n webhook ──► Roboflow API (YOLOv8) ──► circuit analysis ──► LLM chatbot ──► JSON response
                                            │  BOM, designators,          │  explanation +
                                            │  design-rule checks         │  optimizations
                                            ▼                             ▼
                                     digital-twin JSON ──────────► Unity 3D twin
```

| Part | Where | Role |
|---|---|---|
| Detection | Roboflow hosted YOLOv8 (`training/`) | Locate and classify resistors, capacitors, ICs, LEDs, crystals, connectors… |
| Orchestration | `n8n/` | Webhook → inference → analysis → LLM → response, plus a follow-up chat workflow |
| Analysis | `pcb_inspector/analysis.py` | Reference designators (R1, C2, U1…), BOM, design checks, quality score |
| Chatbot | `pcb_inspector/chatbot.py` | Grounded explanation and prioritized optimizations (Anthropic or OpenAI-compatible API, offline fallback) |
| Digital twin | `pcb_inspector/twin.py`, `unity/` | Pixel → millimetre mapping, Unity scene with status colours and click-to-inspect |

## Design checks

| Check | Why it matters |
|---|---|
| Every IC has a decoupling capacitor nearby | Missing decoupling causes supply noise and resets |
| Every LED has a series resistor nearby | Prevents over-current |
| Crystal placed close to its IC | Long traces destabilize the oscillator |
| Overlapping boxes with different classes | Ambiguous detection, routed to human review |
| Detection confidence below 60 % | Flagged for visual confirmation |
| Comparison with an expected BOM | Missing or extra parts on the assembly line |

Each component gets a status (ok, review, issue) and the board gets a quality score, which drive both the chatbot priorities and the twin colours.

## Example output (sample board)

```
BOM: capacitor 4, connector 1, crystal 1, diode 1, electrolytic capacitor 1, ic 2, led 2, resistor 2, switch 1, transistor 1
Quality score: 75/100

Priority actions:
- [ISSUE]  U1: no decoupling capacitor nearby, add 100 nF close to VCC/GND
- [REVIEW] D3: check for a current-limiting resistor
```

## Run it

```bash
pip install -r ../requirements.txt

# Offline demo on saved Roboflow detections
python inspect_board.py --detections samples/sample_detections.json

# Live inference with your Roboflow model
export ROBOFLOW_API_KEY=...
python inspect_board.py --image board.jpg --model pcb-components --version 3

# LLM explanation and follow-up questions
export ANTHROPIC_API_KEY=...        # or OPENAI_API_KEY (+ OPENAI_BASE_URL)
python inspect_board.py --detections samples/sample_detections.json --question "How can I make this board more robust to ESD?"
```

Outputs: `output/analysis.json`, `output/digital_twin.json`, `output/detections.png`.

- **n8n:** import the two workflows from [`n8n/`](n8n/) and set the environment variables listed in [`n8n/README.md`](n8n/README.md).
- **Unity:** copy [`unity/`](unity/) into a project and press Play, see [`unity/README.md`](unity/README.md).
- **Training:** dataset, augmentation and YOLOv8 fine-tuning in [`training/`](training/).

## Testing

`tests/test_pcb.py` covers parsing, designators, every design check, the twin coordinate mapping, the structure of both n8n workflows, and runs the n8n JavaScript analysis node with Node.js to confirm it matches the Python version.

## Files

```
pcb_inspector/        detections + Roboflow client, analysis, chatbot, digital-twin export
inspect_board.py      command-line inspection
n8n/                  importable workflows (inspection + chatbot)
tools/                generator for the n8n workflow JSON
unity/                C# scripts and a sample twin for Unity
training/             YOLOv8 training on a Roboflow dataset
samples/              saved Roboflow response for offline runs
```
