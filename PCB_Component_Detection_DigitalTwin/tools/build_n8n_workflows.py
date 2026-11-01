"""Generate the importable n8n workflow JSON files in ../n8n/.

The workflows are generated from code so the JavaScript in the Code nodes and the
LLM system prompt stay in sync with the Python package. Run:  python tools/build_n8n_workflows.py
"""
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pcb_inspector.chatbot import SYSTEM_PROMPT  # noqa: E402

ANALYZE_JS = r"""// Port of pcb_inspector/analysis.py + twin.py for n8n
const req = $('Receive board image').first().json.body || {};
const rf = $input.first().json;
const W = rf.image?.width || 1, H = rf.image?.height || 1;
const canon = { 'res':'resistor','resistor':'resistor','cap':'capacitor','capacitor':'capacitor',
  'ceramic capacitor':'capacitor','electrolytic capacitor':'electrolytic_capacitor','electrolytic':'electrolytic_capacitor',
  'ic':'ic','chip':'ic','microcontroller':'ic','integrated circuit':'ic','transistor':'transistor','mosfet':'transistor',
  'diode':'diode','led':'led','inductor':'inductor','coil':'inductor','connector':'connector','header':'connector',
  'usb':'connector','crystal':'crystal','oscillator':'crystal','button':'switch','switch':'switch' };
const prefix = { resistor:'R', capacitor:'C', electrolytic_capacitor:'C', ic:'U', transistor:'Q', diode:'D', led:'D',
  inductor:'L', connector:'J', crystal:'Y', switch:'SW' };
const prefab = { resistor:'Resistor_0805', capacitor:'Capacitor_0805', electrolytic_capacitor:'Capacitor_Electrolytic',
  ic:'IC_QFP', transistor:'Transistor_SOT23', diode:'Diode_SOD123', led:'LED_0805', inductor:'Inductor_SMD',
  connector:'Connector_Header', crystal:'Crystal_HC49', switch:'Switch_Tactile' };
const colors = { ok:'#2E9E6A', review:'#E8A33D', issue:'#D64545' };
const rank = { ok:0, review:1, issue:2 };

const preds = (rf.predictions || []).map(p => ({ ...p, type: canon[p.class.trim().toLowerCase()] || p.class.trim().toLowerCase() }));
const rowH = Math.max(1, ...preds.map(p => p.height));
preds.sort((a, b) => Math.round(a.y / rowH) - Math.round(b.y / rowH) || a.x - b.x);
const counters = {};
const comps = preds.map(p => {
  const pre = prefix[p.type] || 'X';
  counters[pre] = (counters[pre] || 0) + 1;
  return { ref: pre + counters[pre], type: p.type, confidence: p.confidence, x: p.x, y: p.y,
           width: p.width, height: p.height, status: 'ok', notes: [] };
});
const flag = (c, s, n) => { if (rank[s] > rank[c.status]) c.status = s; c.notes.push(n); };
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
const findings = [];
const caps = comps.filter(c => c.type.includes('capacitor'));
const resistors = comps.filter(c => c.type === 'resistor');

comps.filter(c => c.confidence < 0.6).forEach(c => flag(c, 'review', `low detection confidence (${Math.round(c.confidence*100)}%), confirm visually`));
comps.filter(c => c.type === 'ic').forEach(ic => {
  const reach = 1.5 * Math.hypot(ic.width, ic.height);
  if (!caps.some(cap => dist(ic, cap) <= reach)) {
    flag(ic, 'issue', 'no decoupling capacitor detected near the supply pins');
    findings.push({ severity: 'issue', ref: ic.ref, message: `${ic.ref}: no decoupling capacitor nearby, add 100 nF close to VCC/GND` });
  }
});
comps.filter(c => c.type === 'led').forEach(led => {
  const reach = 4 * Math.max(led.width, led.height);
  if (!resistors.some(r => dist(led, r) <= reach)) {
    flag(led, 'review', 'no series resistor detected nearby');
    findings.push({ severity: 'review', ref: led.ref, message: `${led.ref}: check for a current-limiting resistor` });
  }
});
const expected = req.expected_bom || null;
const bom = {};
comps.forEach(c => bom[c.type] = (bom[c.type] || 0) + 1);
if (expected) for (const [t, q] of Object.entries(expected)) {
  const f = bom[t] || 0;
  if (f < q) findings.push({ severity: 'issue', ref: t, message: `missing ${q - f} x ${t} vs expected BOM` });
}
const nIssue = comps.filter(c => c.status === 'issue').length, nReview = comps.filter(c => c.status === 'review').length;
const analysis = { image: { width: W, height: H }, component_count: comps.length, bom, components: comps, findings,
  quality_score: Math.max(0, 100 - 15 * nIssue - 5 * nReview), needs_human_review: nIssue + nReview > 0 };

const boardW = Number(req.board_width_mm || 100), scale = boardW / W, boardH = H * scale;
const twin = { schema: 'pcb-digital-twin/1', board: { name: req.board_name || 'pcb', width_mm: boardW, height_mm: +boardH.toFixed(2) },
  quality_score: analysis.quality_score, findings,
  components: comps.map(c => ({ ref: c.ref, type: c.type, prefab: prefab[c.type] || 'Generic_Component',
    x_mm: +(c.x * scale).toFixed(2), y_mm: +(boardH - c.y * scale).toFixed(2),
    width_mm: +(c.width * scale).toFixed(2), length_mm: +(c.height * scale).toFixed(2),
    rotation_deg: c.height > c.width * 1.3 ? 90 : 0, status: c.status, color: colors[c.status],
    confidence: c.confidence, notes: c.notes })) };

return [{ json: { analysis, digital_twin: twin, question: req.question || 'Explain what this circuit does and list the top optimizations.' } }];
"""

RESPONSE_JS = r"""const prev = $('Analyze circuit').first().json;
const llm = $input.first().json;
const explanation = (llm.content || []).map(b => b.text || '').join('') || llm.choices?.[0]?.message?.content || '';
return [{ json: { ...prev.analysis, explanation, digital_twin: prev.digital_twin } }];
"""

CHAT_JS = r"""// Builds the conversation for a follow-up question about an analyzed board
const body = $input.first().json.body || {};
const context = 'PCB analysis:\n```json\n' + JSON.stringify(body.analysis || {}, null, 1) + '\n```';
const history = Array.isArray(body.history) ? body.history : [];
const messages = history.length
  ? [{ role: 'user', content: context }, { role: 'assistant', content: 'Analysis received.' }, ...history,
     { role: 'user', content: body.question || 'Continue.' }]
  : [{ role: 'user', content: context + '\n\n' + (body.question || 'Explain this circuit.') }];
return [{ json: { messages } }];
"""

CHAT_REPLY_JS = r"""const llm = $input.first().json;
const answer = (llm.content || []).map(b => b.text || '').join('');
const asked = $('Build conversation').first().json.messages;
return [{ json: { answer, history: [...asked.slice(-1), { role: 'assistant', content: answer }] } }];
"""


def node(name, ntype, version, position, parameters, **extra):
    return {"parameters": parameters, "id": str(uuid.uuid5(uuid.NAMESPACE_URL, name)), "name": name,
            "type": ntype, "typeVersion": version, "position": position, **extra}


def anthropic_request(name, position, messages_expr):
    return node(name, "n8n-nodes-base.httpRequest", 4.2, position, {
        "method": "POST",
        "url": "https://api.anthropic.com/v1/messages",
        "sendHeaders": True,
        "headerParameters": {"parameters": [
            {"name": "x-api-key", "value": "={{ $env.ANTHROPIC_API_KEY }}"},
            {"name": "anthropic-version", "value": "2023-06-01"},
        ]},
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify({ model: $env.LLM_MODEL || 'claude-haiku-5-5', max_tokens: 1024, "
                    f"system: {json.dumps(SYSTEM_PROMPT)}, messages: {messages_expr} }}) }}}}",
        "options": {"timeout": 60000},
    })


def link(*names):
    return {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(names, names[1:], strict=False)}


def inspection_workflow():
    names = ["Receive board image", "Roboflow YOLO inference", "Analyze circuit", "LLM circuit explanation",
             "Build response", "Respond with analysis"]
    nodes = [
        node(names[0], "n8n-nodes-base.webhook", 2, [0, 300],
             {"httpMethod": "POST", "path": "pcb-inspect", "responseMode": "responseNode", "options": {}},
             webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, "pcb-inspect"))),
        node(names[1], "n8n-nodes-base.httpRequest", 4.2, [240, 300], {
            "method": "POST",
            "url": "={{ ($env.ROBOFLOW_API_URL || 'https://detect.roboflow.com') + '/' + $env.ROBOFLOW_MODEL "
                   "+ '/' + $env.ROBOFLOW_VERSION }}",
            "sendQuery": True,
            "queryParameters": {"parameters": [
                {"name": "api_key", "value": "={{ $env.ROBOFLOW_API_KEY }}"},
                {"name": "image", "value": "={{ $json.body.image_url }}"},
                {"name": "confidence", "value": "40"},
                {"name": "overlap", "value": "30"},
            ]},
            "options": {"timeout": 30000},
        }),
        node(names[2], "n8n-nodes-base.code", 2, [480, 300], {"jsCode": ANALYZE_JS}),
        anthropic_request(names[3], [720, 300], "[{ role: 'user', content: 'PCB analysis:\\n' + "
                          "JSON.stringify($json.analysis, null, 1) + '\\n\\n' + $json.question }]"),
        node(names[4], "n8n-nodes-base.code", 2, [960, 300], {"jsCode": RESPONSE_JS}),
        node(names[5], "n8n-nodes-base.respondToWebhook", 1.1, [1200, 300],
             {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}}),
    ]
    return {"name": "PCB Inspection: YOLO (Roboflow) + Circuit Analysis + LLM + Digital Twin",
            "nodes": nodes, "connections": link(*names), "settings": {"executionOrder": "v1"},
            "pinData": {}, "active": False}


def chat_workflow():
    names = ["Receive question", "Build conversation", "LLM circuit chatbot", "Format answer", "Respond with answer"]
    nodes = [
        node(names[0], "n8n-nodes-base.webhook", 2, [0, 300],
             {"httpMethod": "POST", "path": "pcb-chat", "responseMode": "responseNode", "options": {}},
             webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, "pcb-chat"))),
        node(names[1], "n8n-nodes-base.code", 2, [240, 300], {"jsCode": CHAT_JS}),
        anthropic_request(names[2], [480, 300], "$json.messages"),
        node(names[3], "n8n-nodes-base.code", 2, [720, 300], {"jsCode": CHAT_REPLY_JS}),
        node(names[4], "n8n-nodes-base.respondToWebhook", 1.1, [960, 300],
             {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}}),
    ]
    return {"name": "PCB Circuit Chatbot: explanation and optimization",
            "nodes": nodes, "connections": link(*names), "settings": {"executionOrder": "v1"},
            "pinData": {}, "active": False}


if __name__ == "__main__":
    out = ROOT / "n8n"
    out.mkdir(exist_ok=True)
    (out / "pcb_inspection_workflow.json").write_text(json.dumps(inspection_workflow(), indent=2))
    (out / "pcb_chatbot_workflow.json").write_text(json.dumps(chat_workflow(), indent=2))
    print("Wrote", *sorted(p.name for p in out.glob("*.json")))
