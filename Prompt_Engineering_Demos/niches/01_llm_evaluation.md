# LLM Evaluation & Benchmarking

Prompts for scoring, comparing and stress-testing model outputs.

## 1. Rubric-based response grader

```text
You are a strict evaluator. Score the response below against the rubric.

User request: """{prompt}"""
Response: """{response}"""

Rubric (1–5 each):
- Correctness: every factual claim is accurate.
- Completeness: all parts of the request are addressed.
- Instruction following: all constraints (format, length, tone) are respected.
- Clarity: easy to follow, no filler.

For each criterion, quote the part of the response that justifies your score,
then give the score. End with one JSON line:
{"correctness": n, "completeness": n, "instruction_following": n, "clarity": n}
```

> **Why it works:** evidence before scores reduces impression-based grading; the JSON line is machine-readable.

## 2. Pairwise preference judge

```text
Compare two responses to the same request and pick the better one.

Request: """{prompt}"""
Response A: """{response_a}"""
Response B: """{response_b}"""

Judge on helpfulness, accuracy and instruction following — not length or style.
If both are equally good or equally bad, answer "tie".
Explain your reasoning in at most 3 sentences, then output:
{"winner": "A" | "B" | "tie"}
```

> **Why it works:** an explicit "tie" option and an anti-length instruction counter two known judge biases. Run it twice with A/B swapped.

## 3. Hallucination detector

```text
Below is a source document and a model-generated summary.

Source: """{source}"""
Summary: """{summary}"""

List every claim in the summary. For each one, label it:
- SUPPORTED: stated or directly implied by the source
- CONTRADICTED: conflicts with the source
- UNSUPPORTED: not in the source (even if true in the real world)

Return JSON: {"claims": [{"claim": "...", "label": "...", "evidence": "<quote or null>"}],
              "hallucination_rate": <unsupported+contradicted / total>}
```

> **Why it works:** claim-level labels make faithfulness measurable instead of a yes/no guess.

## 4. Test-case generator for a capability

```text
I am building an evaluation set for this capability: {capability}
(example: "converting natural-language dates into ISO 8601").

Generate 20 test cases as JSONL, one per line: {"input": "...", "expected": "...", "difficulty": "easy|medium|hard", "tests": "<what edge case it covers>"}

Cover: typical cases, boundary values, ambiguous inputs, malformed inputs,
multilingual inputs (French and Arabic), and at least 3 adversarial cases.
Do not repeat the same pattern twice.
```

> **Why it works:** asking for the edge case each item covers forces diversity and makes the set auditable.

## 5. Failure-mode analysis of an eval run

```text
Here are the failed cases from an evaluation run (input, expected, model output):

{failures_jsonl}

Group the failures into 3–6 failure modes. For each mode give:
- a short name
- how many cases fall into it and their IDs
- the likely root cause (prompt wording, missing knowledge, format drift, reasoning error…)
- one concrete change to the prompt or data that would fix it

Order modes by how many cases they affect.
```

> **Why it works:** turns a list of errors into prioritized, actionable fixes.
