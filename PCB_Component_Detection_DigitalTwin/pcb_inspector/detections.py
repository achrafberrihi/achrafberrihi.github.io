"""Detection model and Roboflow hosted-inference client."""
from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

ROBOFLOW_API_URL = os.environ.get("ROBOFLOW_API_URL", "https://detect.roboflow.com")


@dataclass(frozen=True)
class Detection:
    """One detected component. Coordinates are in pixels, (x, y) is the box centre."""
    label: str
    confidence: float
    x: float
    y: float
    width: float
    height: float
    detection_id: str = ""

    @property
    def box(self) -> tuple[float, float, float, float]:
        return (self.x - self.width / 2, self.y - self.height / 2, self.x + self.width / 2, self.y + self.height / 2)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class InferenceResult:
    image_width: int
    image_height: int
    detections: list[Detection]


def parse_roboflow(payload: dict, min_confidence: float = 0.0) -> InferenceResult:
    """Parse a Roboflow object-detection response (`predictions` + `image`)."""
    image = payload.get("image", {})
    dets = [
        Detection(
            label=p["class"].strip().lower(),
            confidence=float(p["confidence"]),
            x=float(p["x"]), y=float(p["y"]),
            width=float(p["width"]), height=float(p["height"]),
            detection_id=str(p.get("detection_id", i)),
        )
        for i, p in enumerate(payload.get("predictions", []))
        if float(p["confidence"]) >= min_confidence
    ]
    return InferenceResult(int(image.get("width", 0)), int(image.get("height", 0)), dets)


def infer_image(image: str | Path, model_id: str, version: int | str, api_key: str | None = None,
                confidence: int = 40, overlap: int = 30, timeout: float = 30.0) -> InferenceResult:
    """Run a YOLO model hosted on Roboflow on a local image path or an image URL."""
    import requests

    api_key = api_key or os.environ["ROBOFLOW_API_KEY"]
    url = f"{ROBOFLOW_API_URL}/{model_id}/{version}"
    params = {"api_key": api_key, "confidence": confidence, "overlap": overlap, "format": "json"}

    image = str(image)
    if image.startswith(("http://", "https://")):
        resp = requests.post(url, params={**params, "image": image}, timeout=timeout)
    else:
        encoded = base64.b64encode(Path(image).read_bytes()).decode()
        resp = requests.post(url, params=params, data=encoded,
                             headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=timeout)
    resp.raise_for_status()
    return parse_roboflow(resp.json())


def load_detections(path: str | Path) -> InferenceResult:
    """Load a saved Roboflow JSON response (used for offline demos and tests)."""
    return parse_roboflow(json.loads(Path(path).read_text(encoding="utf-8")))
