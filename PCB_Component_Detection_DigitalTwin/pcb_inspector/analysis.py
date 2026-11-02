"""Turn raw detections into a circuit-level analysis: BOM, reference designators and design checks."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from .detections import Detection, InferenceResult

CANONICAL = {
    "resistor": "resistor", "res": "resistor",
    "capacitor": "capacitor", "cap": "capacitor", "ceramic capacitor": "capacitor",
    "electrolytic capacitor": "electrolytic_capacitor", "electrolytic": "electrolytic_capacitor",
    "ic": "ic", "chip": "ic", "microcontroller": "ic", "integrated circuit": "ic",
    "transistor": "transistor", "mosfet": "transistor",
    "diode": "diode", "led": "led", "inductor": "inductor", "coil": "inductor",
    "connector": "connector", "header": "connector", "usb": "connector",
    "crystal": "crystal", "oscillator": "crystal", "button": "switch", "switch": "switch",
}
PREFIX = {"resistor": "R", "capacitor": "C", "electrolytic_capacitor": "C", "ic": "U", "transistor": "Q",
          "diode": "D", "led": "D", "inductor": "L", "connector": "J", "crystal": "Y", "switch": "SW"}

LOW_CONFIDENCE = 0.60


@dataclass
class Component:
    ref: str
    type: str
    detection: Detection
    status: str = "ok"                 # ok | review | issue
    notes: list[str] = field(default_factory=list)

    def flag(self, status: str, note: str) -> None:
        rank = {"ok": 0, "review": 1, "issue": 2}
        if rank[status] > rank[self.status]:
            self.status = status
        self.notes.append(note)


def canonical(label: str) -> str:
    return CANONICAL.get(label.strip().lower(), label.strip().lower().replace(" ", "_"))


def _centre_distance(a: Detection, b: Detection) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def _iou(a: Detection, b: Detection) -> float:
    ax1, ay1, ax2, ay2 = a.box
    bx1, by1, bx2, by2 = b.box
    iw, ih = max(0.0, min(ax2, bx2) - max(ax1, bx1)), max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = iw * ih
    union = a.width * a.height + b.width * b.height - inter
    return inter / union if union else 0.0


def assign_references(result: InferenceResult) -> list[Component]:
    """Give each part a designator (R1, C2, U1…) in reading order: top-to-bottom, left-to-right."""
    row_height = max((d.height for d in result.detections), default=1.0)
    ordered = sorted(result.detections, key=lambda d: (round(d.y / row_height), d.x))
    counters: Counter = Counter()
    comps = []
    for d in ordered:
        ctype = canonical(d.label)
        prefix = PREFIX.get(ctype, "X")
        counters[prefix] += 1
        comps.append(Component(f"{prefix}{counters[prefix]}", ctype, d))
    return comps


def run_checks(comps: list[Component], expected_bom: dict[str, int] | None = None) -> list[dict]:
    """Design-rule style checks a reviewer would do by eye. Returns board-level findings."""
    findings: list[dict] = []
    caps = [c for c in comps if c.type in ("capacitor", "electrolytic_capacitor")]
    resistors = [c for c in comps if c.type == "resistor"]
    ics = [c for c in comps if c.type == "ic"]

    for c in comps:
        if c.detection.confidence < LOW_CONFIDENCE:
            c.flag("review", f"low detection confidence ({c.detection.confidence:.0%}), confirm visually")

    for ic in ics:  # decoupling capacitor close to every IC
        reach = 1.5 * math.hypot(ic.detection.width, ic.detection.height)
        if not any(_centre_distance(ic.detection, cap.detection) <= reach for cap in caps):
            ic.flag("issue", "no decoupling capacitor detected near the supply pins")
            findings.append({"severity": "issue", "ref": ic.ref,
                             "message": f"{ic.ref}: no decoupling capacitor nearby, add 100 nF close to VCC/GND"})

    for led in (c for c in comps if c.type == "led"):  # current-limiting resistor
        reach = 4 * max(led.detection.width, led.detection.height)
        if not any(_centre_distance(led.detection, r.detection) <= reach for r in resistors):
            led.flag("review", "no series resistor detected nearby")
            findings.append({"severity": "review", "ref": led.ref,
                             "message": f"{led.ref}: check for a current-limiting resistor"})

    for xtal in (c for c in comps if c.type == "crystal"):  # crystal should sit next to its IC
        if ics and min(_centre_distance(xtal.detection, ic.detection) for ic in ics) > 3 * max(
                xtal.detection.width, xtal.detection.height) + max(ics[0].detection.width, ics[0].detection.height):
            xtal.flag("review", "crystal far from the IC, long traces can affect oscillation")
            findings.append({"severity": "review", "ref": xtal.ref,
                             "message": f"{xtal.ref}: place the crystal closer to its IC"})

    for i, a in enumerate(comps):  # overlapping boxes with different labels = ambiguous detection
        for b in comps[i + 1:]:
            if a.type != b.type and _iou(a.detection, b.detection) > 0.5:
                for c in (a, b):
                    c.flag("review", f"overlaps {b.ref if c is a else a.ref}, ambiguous class")
                findings.append({"severity": "review", "ref": f"{a.ref}/{b.ref}",
                                 "message": f"{a.ref} and {b.ref} overlap with different classes"})

    if expected_bom:
        found = Counter(c.type for c in comps)
        for ctype, qty in expected_bom.items():
            if found.get(ctype, 0) < qty:
                findings.append({"severity": "issue", "ref": ctype,
                                 "message": f"missing {qty - found.get(ctype, 0)} × {ctype} vs expected BOM"})
            elif found.get(ctype, 0) > qty:
                findings.append({"severity": "review", "ref": ctype,
                                 "message": f"{found[ctype] - qty} extra {ctype} vs expected BOM"})
    return findings


def analyze(result: InferenceResult, expected_bom: dict[str, int] | None = None) -> dict:
    comps = assign_references(result)
    findings = run_checks(comps, expected_bom)
    status_counts = Counter(c.status for c in comps)
    score = 100 - 15 * status_counts.get("issue", 0) - 5 * status_counts.get("review", 0)
    return {
        "image": {"width": result.image_width, "height": result.image_height},
        "component_count": len(comps),
        "bom": dict(sorted(Counter(c.type for c in comps).items())),
        "components": [
            {"ref": c.ref, "type": c.type, "confidence": round(c.detection.confidence, 3),
             "x": c.detection.x, "y": c.detection.y, "width": c.detection.width, "height": c.detection.height,
             "status": c.status, "notes": c.notes}
            for c in comps
        ],
        "findings": findings,
        "quality_score": max(0, score),
        "needs_human_review": status_counts.get("review", 0) > 0 or status_counts.get("issue", 0) > 0,
    }
