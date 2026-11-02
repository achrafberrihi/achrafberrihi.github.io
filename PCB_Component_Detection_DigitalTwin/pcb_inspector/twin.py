"""Export an analysis as a digital-twin scene description for Unity."""
from __future__ import annotations

PREFABS = {
    "resistor": "Resistor_0805", "capacitor": "Capacitor_0805", "electrolytic_capacitor": "Capacitor_Electrolytic",
    "ic": "IC_QFP", "transistor": "Transistor_SOT23", "diode": "Diode_SOD123", "led": "LED_0805",
    "inductor": "Inductor_SMD", "connector": "Connector_Header", "crystal": "Crystal_HC49", "switch": "Switch_Tactile",
}
STATUS_COLORS = {"ok": "#2E9E6A", "review": "#E8A33D", "issue": "#D64545"}


def to_digital_twin(analysis: dict, board_width_mm: float = 100.0, board_name: str = "pcb") -> dict:
    """Map pixel detections onto board coordinates in millimetres (origin at bottom-left, like Unity's x/z plane)."""
    img_w = analysis["image"]["width"] or 1
    img_h = analysis["image"]["height"] or 1
    scale = board_width_mm / img_w
    board_height_mm = img_h * scale

    components = []
    for c in analysis["components"]:
        components.append({
            "ref": c["ref"],
            "type": c["type"],
            "prefab": PREFABS.get(c["type"], "Generic_Component"),
            "x_mm": round(c["x"] * scale, 2),
            "y_mm": round(board_height_mm - c["y"] * scale, 2),     # flip image y-axis
            "width_mm": round(c["width"] * scale, 2),
            "length_mm": round(c["height"] * scale, 2),
            "rotation_deg": 90.0 if c["height"] > c["width"] * 1.3 else 0.0,
            "status": c["status"],
            "color": STATUS_COLORS[c["status"]],
            "confidence": c["confidence"],
            "notes": c["notes"],
        })

    return {
        "schema": "pcb-digital-twin/1",
        "board": {"name": board_name, "width_mm": board_width_mm, "height_mm": round(board_height_mm, 2)},
        "quality_score": analysis["quality_score"],
        "components": components,
        "findings": analysis["findings"],
    }
