"""Minimal LLM evaluation harness.

Runs prompt templates over labelled datasets, scores each output and prints a
report with per-task accuracy and every failure, so prompt changes can be
compared on numbers instead of impressions.

    python eval_harness.py                                   # replay recorded outputs (no API key)
    python eval_harness.py --model anthropic:claude-haiku-5-5
    python eval_harness.py --model openai:gpt-4o-mini --task sentiment

Templates use {placeholders} filled from each case's "input"; other braces
(e.g. JSON schemas) are left untouched.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent

TASKS = {
    "sentiment": {"prompt": "prompts/sentiment.txt", "dataset": "datasets/sentiment.jsonl", "scorer": "exact"},
    "invoice_extraction": {
        "prompt": "prompts/invoice_extraction.txt",
        "dataset": "datasets/invoice_extraction.jsonl",
        "scorer": "json_fields",
    },
}


# ── Templating ──────────────────────────────────────────────────────────────
def render(template: str, values: dict[str, Any]) -> str:
    """Fill {name} placeholders that exist in `values`; leave every other brace alone."""
    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in values:
            return m.group(0)
        return str(values[key])
    return re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", sub, template)


# ── Scorers: return (score in [0, 1], short note) ───────────────────────────
def normalise_label(text: str) -> str:
    return re.sub(r"[^a-z_]", "", text.strip().lower().split("\n")[0])


def score_exact(output: str, expected: str) -> tuple[float, str]:
    got = normalise_label(output)
    return (1.0, "") if got == normalise_label(expected) else (0.0, f"got {got!r}")


def parse_json(output: str) -> Any:
    """Parse JSON even if the model wrapped it in markdown fences or added text around it."""
    text = output.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        obj = re.search(r"\{.*\}", text, re.S)
        if obj:
            return json.loads(obj.group(0))
        raise


def values_match(got: Any, want: Any) -> bool:
    if isinstance(want, (int, float)) and isinstance(got, (int, float)) and not isinstance(got, bool):
        return math.isclose(float(got), float(want), rel_tol=1e-6, abs_tol=1e-6)
    if isinstance(want, str) and isinstance(got, str):
        return got.strip() == want.strip()
    return got == want


def score_json_fields(output: str, expected: dict) -> tuple[float, str]:
    """Field-level accuracy; a hallucinated value where null was expected counts as wrong."""
    try:
        got = parse_json(output)
    except (json.JSONDecodeError, ValueError):
        return 0.0, "invalid JSON"
    if not isinstance(got, dict):
        return 0.0, "JSON is not an object"
    wrong = [k for k, v in expected.items() if not values_match(got.get(k), v)]
    note = ", ".join(f"{k}: got {got.get(k)!r}, want {expected[k]!r}" for k in wrong)
    return 1 - len(wrong) / len(expected), note


SCORERS: dict[str, Callable[[str, Any], tuple[float, str]]] = {"exact": score_exact, "json_fields": score_json_fields}


# ── Model backends ──────────────────────────────────────────────────────────
def make_backend(spec: str) -> Callable[[str, dict], str]:
    provider, _, model = spec.partition(":")

    if provider == "mock":
        # Replays the recorded output stored with each case — exercises the full
        # scoring pipeline offline and in CI.
        return lambda prompt, case: case.get("mock_output", "")

    if provider == "anthropic":
        import anthropic  # pip install anthropic
        client = anthropic.Anthropic()
        def call(prompt: str, case: dict) -> str:
            msg = client.messages.create(model=model or "claude-haiku-5-5", max_tokens=512, temperature=0,
                                         messages=[{"role": "user", "content": prompt}])
            return "".join(b.text for b in msg.content if b.type == "text")
        return call

    if provider == "openai":
        from openai import OpenAI  # pip install openai
        client = OpenAI()
        def call(prompt: str, case: dict) -> str:
            resp = client.chat.completions.create(model=model or "gpt-4o-mini", temperature=0,
                                                  messages=[{"role": "user", "content": prompt}])
            return resp.choices[0].message.content or ""
        return call

    raise SystemExit(f"Unknown backend {spec!r}. Use mock, anthropic:<model> or openai:<model>.")


def with_retries(fn: Callable[[], str], attempts: int = 3) -> str:
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # network / rate-limit errors from any SDK
            if i == attempts - 1:
                return f"<<error: {exc}>>"
            time.sleep(2 ** i)
    return ""


# ── Runner ──────────────────────────────────────────────────────────────────
@dataclass
class Result:
    task: str
    case_id: str
    score: float
    note: str
    output: str


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_task(name: str, backend: Callable[[str, dict], str], workers: int) -> list[Result]:
    cfg = TASKS[name]
    template = (HERE / cfg["prompt"]).read_text(encoding="utf-8")
    cases = load_jsonl(HERE / cfg["dataset"])
    scorer = SCORERS[cfg["scorer"]]

    def evaluate(case: dict) -> Result:
        prompt = render(template, case["input"])
        output = with_retries(lambda: backend(prompt, case))
        score, note = scorer(output, case["expected"])
        return Result(name, case["id"], round(score, 3), note, output)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(evaluate, cases))


def report(results: list[Result]) -> float:
    by_task: dict[str, list[Result]] = {}
    for r in results:
        by_task.setdefault(r.task, []).append(r)

    print(f"\n{'task':<22}{'cases':>7}{'score':>9}{'perfect':>10}")
    print("-" * 48)
    for task, rs in by_task.items():
        mean = sum(r.score for r in rs) / len(rs)
        perfect = sum(r.score == 1 for r in rs)
        print(f"{task:<22}{len(rs):>7}{mean:>9.1%}{perfect:>6}/{len(rs)}")

    failures = [r for r in results if r.score < 1]
    if failures:
        print("\nFailures:")
        for r in failures:
            print(f"  [{r.task}/{r.case_id}] score={r.score:.2f}  {r.note}")
    overall = sum(r.score for r in results) / len(results)
    print(f"\nOverall: {overall:.1%}\n")
    return overall


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="mock", help="mock | anthropic:<model> | openai:<model>")
    parser.add_argument("--task", choices=TASKS, action="append", help="run only this task (repeatable)")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--min-score", type=float, default=0.0, help="exit 1 if overall score is below this (for CI)")
    parser.add_argument("--save", type=Path, help="write per-case results to this JSON file")
    args = parser.parse_args()

    backend = make_backend(args.model)
    results = [r for t in (args.task or TASKS) for r in run_task(t, backend, args.workers)]
    print(f"Model: {args.model}")
    overall = report(results)

    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved results to {args.save}")
    if overall < args.min_score:
        sys.exit(1)


if __name__ == "__main__":
    main()
