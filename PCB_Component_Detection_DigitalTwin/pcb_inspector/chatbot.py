"""Circuit explanation and optimization chatbot.

Uses an LLM when an API key is configured (Anthropic by default, or any
OpenAI-compatible endpoint), and falls back to a deterministic explanation
built from the analysis so the demo works offline.
"""
from __future__ import annotations

import json
import os

SYSTEM_PROMPT = """You are an electronics design assistant reviewing a PCB from automated component detection.

You receive a JSON analysis: bill of materials, components with reference designators, positions
in pixels, detection confidence, and design-check findings.

Rules:
- Base every statement on the analysis. Detection can be wrong: when confidence is below 60 % or a
  finding says "review", say it needs visual confirmation instead of asserting it.
- Explain what the circuit most likely does from its parts (e.g. MCU + crystal + decoupling caps +
  USB connector = microcontroller board), and say how confident you are.
- Give concrete, prioritized optimizations: decoupling, current limiting, placement, thermal,
  manufacturability (DFM), and testability. Reference designators in every suggestion.
- Never invent component values or part numbers that aren't in the data. Suggest typical values only
  when clearly labelled as typical (e.g. "typically 100 nF").
- Be concise: short paragraphs and bullet points. Answer in the user's language."""


def build_messages(analysis: dict, question: str | None = None, history: list[dict] | None = None) -> list[dict]:
    context = "PCB analysis:\n```json\n" + json.dumps(analysis, ensure_ascii=False, indent=1) + "\n```"
    first = f"{context}\n\n{question or 'Explain what this circuit does and list the top optimizations.'}"
    if not history:
        return [{"role": "user", "content": first}]
    return [{"role": "user", "content": context}, {"role": "assistant", "content": "Analysis received."},
            *history, {"role": "user", "content": question or "Continue."}]


def _call_anthropic(messages: list[dict], model: str, api_key: str, timeout: float) -> str:
    import requests
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model, "max_tokens": 1024, "system": SYSTEM_PROMPT, "messages": messages},
        timeout=timeout,
    )
    resp.raise_for_status()
    return "".join(b.get("text", "") for b in resp.json()["content"])


def _call_openai_compatible(messages: list[dict], model: str, api_key: str, base_url: str, timeout: float) -> str:
    import requests
    resp = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages]},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def offline_explanation(analysis: dict) -> str:
    """Rule-based explanation used when no LLM is configured."""
    bom = analysis["bom"]
    parts = ", ".join(f"{n} × {t.replace('_', ' ')}" for t, n in bom.items())
    lines = [f"Detected {analysis['component_count']} components: {parts}."]

    if bom.get("ic") and bom.get("crystal"):
        lines.append("An IC with a crystal suggests a microcontroller or clocked digital circuit.")
    if bom.get("connector"):
        lines.append("Connectors indicate external power, programming or I/O interfaces.")
    if bom.get("led"):
        lines.append("LEDs are likely status or power indicators.")

    if analysis["findings"]:
        lines.append("\nPriority actions:")
        order = {"issue": 0, "review": 1}
        for f in sorted(analysis["findings"], key=lambda f: order.get(f["severity"], 2)):
            lines.append(f"- [{f['severity'].upper()}] {f['message']}")
    else:
        lines.append("\nNo design-rule findings. Confirm values and polarity during visual inspection.")
    lines.append(f"\nBoard quality score: {analysis['quality_score']}/100.")
    return "\n".join(lines)


def ask(analysis: dict, question: str | None = None, history: list[dict] | None = None, timeout: float = 60.0) -> str:
    """Return the chatbot answer, using the configured LLM or the offline fallback."""
    messages = build_messages(analysis, question, history)
    model = os.environ.get("LLM_MODEL", "claude-haiku-5-5")
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _call_anthropic(messages, model, os.environ["ANTHROPIC_API_KEY"], timeout)
    if os.environ.get("OPENAI_API_KEY"):
        return _call_openai_compatible(messages, os.environ.get("LLM_MODEL", "gpt-4o-mini"),
                                       os.environ["OPENAI_API_KEY"],
                                       os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"), timeout)
    return offline_explanation(analysis)
