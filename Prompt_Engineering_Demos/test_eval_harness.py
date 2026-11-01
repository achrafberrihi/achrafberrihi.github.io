"""Unit tests for the evaluation harness (run with: pytest)."""
from eval_harness import TASKS, make_backend, render, run_task, score_exact, score_json_fields


def test_render_fills_only_known_placeholders():
    assert render('Schema: {"a": 1} Text: {text} {other}', {"text": "hi"}) == 'Schema: {"a": 1} Text: hi {other}'


def test_exact_is_case_and_punctuation_insensitive():
    assert score_exact("Positive.\n", "positive")[0] == 1.0
    assert score_exact("negative", "positive")[0] == 0.0


def test_json_fields_parses_fenced_json_and_scores_fields():
    expected = {"a": "x", "b": None, "c": 2.5}
    assert score_json_fields('```json\n{"a": "x", "b": null, "c": 2.50}\n```', expected)[0] == 1.0
    score, note = score_json_fields('{"a": "x", "b": "made-up", "c": 2.5}', expected)
    assert round(score, 3) == 0.667 and "b" in note


def test_json_fields_rejects_invalid_json():
    assert score_json_fields("not json", {"a": 1}) == (0.0, "invalid JSON")


def test_mock_run_covers_all_tasks():
    backend = make_backend("mock")
    for task in TASKS:
        results = run_task(task, backend, workers=2)
        assert results and all(0.0 <= r.score <= 1.0 for r in results)
