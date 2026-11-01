# AI Data Operations & Annotation (HITL)

Prompts for guideline writing, QA and running annotation teams.

## 1. Annotation guideline drafter

```text
Write annotation guidelines for this task: {task_description}
Labels: {labels}

Structure:
1. Goal of the task (2 sentences)
2. Definition of each label, with 2 positive and 1 negative example each
3. Decision rules for the 5 most likely ambiguous cases
4. What to do when unsure (escalation rule)
5. Common mistakes to avoid

Write for annotators whose first language may not be English: short sentences, no jargon.
```

> **Why it works:** explicit ambiguity rules are what actually raise inter-annotator agreement.

## 2. Label QA reviewer

```text
You are a QA reviewer checking an annotator's work against the guidelines.

Guidelines: """{guidelines}"""
Item: """{item}"""
Annotator's label: {label}
Annotator's rationale: {rationale}

Decide: "accept", "reject" or "escalate".
If reject, give the correct label and cite the guideline rule that applies.
If the guidelines don't cover this case, choose "escalate" and propose a new rule.
Return JSON: {"decision": "...", "correct_label": "...", "rule": "...", "feedback_for_annotator": "..."}
```

> **Why it works:** citing the rule makes feedback teachable; "escalate" captures guideline gaps instead of hiding them.

## 3. Disagreement adjudicator

```text
Three annotators labeled the same item differently.

Item: """{item}"""
Labels: A = {label_a}, B = {label_b}, C = {label_c}
Guidelines: """{guidelines}"""

1. Explain what each annotator likely focused on.
2. Give the final label according to the guidelines.
3. State whether the disagreement comes from annotator error or from unclear guidelines.
4. If unclear guidelines, write the clarifying sentence to add.
```

> **Why it works:** separates people problems from guideline problems.

## 4. Weekly quality report writer

```text
Write a weekly quality report for the annotation project using these metrics:

{metrics_table}   (annotator, items done, accuracy vs gold, avg time per item, rejection rate)

Include:
- 3-line executive summary for the client
- top performers and annotators needing coaching (with the specific error pattern)
- trend vs last week: {last_week_metrics}
- 3 actions for next week, each with an owner and a measurable target

Tone: factual, constructive, no blame.
```

> **Why it works:** actions with owners and targets make the report drive improvement, not just describe it.

## 5. Gold-set item creator

```text
Create 10 gold-standard items for calibrating annotators on: {task_description}

For each item give: the text, the correct label, a one-sentence justification
referencing the guidelines, and a difficulty (easy/medium/hard).
Include at least 4 hard items built around the ambiguous cases in the guidelines:
"""{guidelines}"""
Return as a Markdown table.
```

> **Why it works:** gold items targeting known ambiguities measure what matters, not just easy agreement.
