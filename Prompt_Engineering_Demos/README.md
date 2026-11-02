# Prompt Engineering & LLM Evaluation

A library of **95 prompts across 19 niches** and 7 in-depth prompt patterns, plus a small harness that measures them on labelled data.

## What's inside

| Path | Contents |
|---|---|
| [`example_prompts.md`](./example_prompts.md) | Index of **95 prompts across 19 niches** + 7 core patterns explained in depth (classification, JSON extraction, RAG, LLM-as-a-judge, red-team labels, ASR QA, agent tool contracts) |
| [`niches/`](./niches) | One file per field: LLM evaluation, data ops, red teaming, RAG, agents, speech/ASR, vision, data/SQL, software, Edge AI, industrial/electrical, marketing, support, education, healthcare, finance, legal, HR, localization (FR/AR/Darija) |
| `prompts/` | Prompt templates used by the harness |
| `datasets/` | Labelled test cases (JSONL), including adversarial ones: sarcasm, French input, missing fields, prompt injection inside a document |
| [`eval_harness.py`](./eval_harness.py) | Runs templates over datasets, scores outputs, reports accuracy and every failure |
| `test_eval_harness.py` | Unit tests for templating and scorers |

## Run it

```bash
pip install -r ../requirements.txt

# Offline: replays recorded model outputs, no API key needed
python eval_harness.py

# Against a real model
export ANTHROPIC_API_KEY=...      # or OPENAI_API_KEY
python eval_harness.py --model anthropic:claude-haiku-5-5
python eval_harness.py --model openai:gpt-4o-mini --task sentiment --save results/run.json
```

Sample report (recorded outputs, which include deliberate mistakes to show failure analysis):

```text
task                    cases    score   perfect
------------------------------------------------
sentiment                   8    87.5%     7/8
invoice_extraction          3    93.3%     2/3

Failures:
  [sentiment/s04] score=0.00  got 'positive'
  [invoice_extraction/i02] score=0.80  invoice_number: got 'R-0001', want None

Overall: 89.1%
```

The two failures are exactly the cases the dataset was built to catch: a **sarcastic** review read literally, and a **hallucinated invoice number** where the document had none.

## How scoring works

- **`exact`**: label classification. Case, whitespace and trailing punctuation are ignored, so format drift ("Positive.") isn't counted as a wrong answer.
- **`json_fields`**: field-level accuracy for extraction. Tolerates markdown fences, compares numbers numerically, and counts an invented value where `null` was expected as an error.

## Adding a task

1. Write a template in `prompts/` using `{placeholders}` (JSON braces are left untouched).
2. Add cases to `datasets/<task>.jsonl`: `{"id", "input": {...}, "expected": ...}`.
3. Register it in `TASKS` in `eval_harness.py` with a scorer.

Use `--min-score 0.9` in CI to fail a build when a prompt change causes a regression.
