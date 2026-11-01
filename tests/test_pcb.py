import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[1] / "PCB_Component_Detection_DigitalTwin"
sys.path.insert(0, str(PROJECT))

from pcb_inspector import analyze, load_detections, parse_roboflow, to_digital_twin  # noqa: E402
from pcb_inspector.chatbot import build_messages, offline_explanation  # noqa: E402

SAMPLE = PROJECT / "samples" / "sample_detections.json"


def pred(cls, x, y, w=30, h=16, conf=0.9):
    return {"class": cls, "confidence": conf, "x": x, "y": y, "width": w, "height": h}


def board(*preds, w=1000, h=800):
    return parse_roboflow({"image": {"width": w, "height": h}, "predictions": list(preds)})


def test_sample_analysis_finds_expected_issues():
    a = analyze(load_detections(SAMPLE))
    assert a["component_count"] == 16
    assert {f["ref"] for f in a["findings"]} == {"U1", "D3"}
    assert a["quality_score"] == 75


def test_designators_follow_reading_order():
    a = analyze(board(pred("resistor", 500, 100), pred("resistor", 100, 100), pred("ic", 300, 500, 100, 100)))
    refs = {c["ref"]: c["x"] for c in a["components"]}
    assert refs["R1"] < refs["R2"] and "U1" in refs


def test_decoupling_check():
    lonely = analyze(board(pred("ic", 300, 300, 100, 100)))
    assert lonely["components"][0]["status"] == "issue"
    ok = analyze(board(pred("ic", 300, 300, 100, 100), pred("capacitor", 380, 300)))
    assert all(c["status"] == "ok" for c in ok["components"])


def test_low_confidence_and_expected_bom():
    a = analyze(board(pred("resistor", 100, 100, conf=0.4)), expected_bom={"resistor": 1, "capacitor": 2})
    assert a["components"][0]["status"] == "review"
    assert any("missing 2 × capacitor" in f["message"] for f in a["findings"])


def test_twin_maps_pixels_to_millimetres_with_flipped_y():
    a = analyze(board(pred("resistor", 100, 700), w=1000, h=800))
    twin = to_digital_twin(a, board_width_mm=50)
    comp = twin["components"][0]
    assert twin["board"]["height_mm"] == 40.0
    assert comp["x_mm"] == 5.0 and comp["y_mm"] == 5.0


def test_chatbot_offline_and_messages():
    a = analyze(load_detections(SAMPLE))
    assert "U1" in offline_explanation(a)
    msgs = build_messages(a, "Q2", history=[{"role": "user", "content": "Q1"}, {"role": "assistant", "content": "A1"}])
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant", "user"]


@pytest.mark.parametrize("name", ["pcb_inspection_workflow.json", "pcb_chatbot_workflow.json"])
def test_n8n_workflows_are_well_formed(name):
    wf = json.loads((PROJECT / "n8n" / name).read_text())
    names = [n["name"] for n in wf["nodes"]]
    assert len(names) == len(set(names))
    assert wf["nodes"][0]["type"] == "n8n-nodes-base.webhook"
    assert wf["nodes"][-1]["type"] == "n8n-nodes-base.respondToWebhook"
    for src, conn in wf["connections"].items():
        assert src in names and all(t["node"] in names for t in conn["main"][0])
    assert len(wf["connections"]) == len(names) - 1   # a single linear chain


def test_n8n_workflows_are_up_to_date():
    import importlib.util
    spec = importlib.util.spec_from_file_location("build", PROJECT / "tools" / "build_n8n_workflows.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    on_disk = json.loads((PROJECT / "n8n" / "pcb_inspection_workflow.json").read_text())
    assert on_disk == json.loads(json.dumps(build.inspection_workflow()))


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_n8n_js_analysis_matches_python(tmp_path):
    wf = json.loads((PROJECT / "n8n" / "pcb_inspection_workflow.json").read_text())
    code = next(n for n in wf["nodes"] if n["name"] == "Analyze circuit")["parameters"]["jsCode"]
    runner = tmp_path / "run.js"
    runner.write_text(
        "const fs=require('fs');const input=JSON.parse(fs.readFileSync(process.argv[2]));"
        "const $input={first:()=>({json:input})};const $=()=>({first:()=>({json:{body:{board_width_mm:100}}})});"
        f"const out=(function($input,$){{{code}}})($input,$);process.stdout.write(JSON.stringify(out[0].json));"
    )
    proc = subprocess.run(["node", str(runner), str(SAMPLE)], capture_output=True, text=True, check=True)
    js = json.loads(proc.stdout)
    py = analyze(load_detections(SAMPLE))
    assert js["analysis"]["bom"] == py["bom"]
    assert [c["status"] for c in js["analysis"]["components"]] == [c["status"] for c in py["components"]]
    for j, p in zip(js["digital_twin"]["components"], to_digital_twin(py)["components"], strict=True):
        for key, value in p.items():
            if isinstance(value, float):
                assert j[key] == pytest.approx(value, abs=0.011), (p["ref"], key)  # JS vs Python rounding
            else:
                assert j[key] == value, (p["ref"], key)
