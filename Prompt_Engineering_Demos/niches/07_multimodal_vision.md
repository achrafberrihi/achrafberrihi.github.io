# Multimodal & Computer Vision

Prompts for image understanding, visual annotation and multimodal data.

## 1. Image annotation QA

```text
You are reviewing bounding-box annotations on an image.

Image: {image}
Annotations: {annotations_json}  (label, x, y, width, height)
Guideline: boxes must be tight, every visible object of the listed classes must be labeled,
occluded objects are labeled if more than 30% is visible.

Report: missing objects, wrong labels, loose boxes, duplicate boxes.
Return JSON: {"issues": [{"type": "...", "object": "...", "fix": "..."}], "verdict": "pass|fail"}
```

> **Why it works:** concrete thresholds (30% visible, tight boxes) make visual QA reproducible.

## 2. Dense image captioning

```text
Describe this image for a training dataset.

Write:
1. A one-sentence caption.
2. A detailed description (4–6 sentences): main subjects, actions, setting, lighting, text visible.
3. A list of objects with approximate positions (left/center/right, foreground/background).
Describe only what is visible. Do not guess identities, brands not shown, or emotions not evident.
```

> **Why it works:** layered captions serve several training uses; the "only visible" rule limits hallucination.

## 3. Driving-scene annotation

```text
Analyze this road scene image from a vehicle's front camera.

List every road user (car, truck, bus, motorcycle, bicycle, pedestrian) and traffic
element (lights and their state, signs, lane markings). For each give: class,
position relative to the ego vehicle, distance (near/mid/far), and whether it could
affect the ego vehicle's next 3 seconds. Return JSON.
```

> **Why it works:** a relevance-to-ego field prioritizes what matters for driving decisions.

## 4. Document image extraction

```text
This is a photo of a {document_type} (e.g. receipt, ID-free invoice, delivery note).

Extract all fields into JSON with this schema: {schema}
- Use null for fields you cannot read with confidence.
- Add "low_confidence_fields": [...] for anything partially legible.
- Preserve original language and formatting of names and numbers.
```

> **Why it works:** explicit low-confidence reporting routes uncertain items to human review.

## 5. Image-text consistency check

```text
Image: {image}
Caption: "{caption}"

Does the caption accurately describe the image? Check each claim in the caption
(objects, counts, colors, actions, text). Return:
{"claims": [{"claim": "...", "status": "correct|wrong|unverifiable"}], "overall": "consistent|inconsistent"}
```

> **Why it works:** claim-by-claim checks catch subtle errors like wrong counts or colors.
