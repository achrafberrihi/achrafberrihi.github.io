# Healthcare (administrative & educational use)

Prompts for health communication, documentation and research support. They do not replace clinical judgment; outputs must be reviewed by qualified professionals.

## 1. Patient-friendly explanation

```text
Explain this medical information to a patient in plain language (reading level: age 12):
"""{medical_text}"""

Keep all facts accurate, explain each medical term in parentheses, and end with
3 questions the patient could ask their doctor. Do not add diagnoses, doses or advice
that isn't in the original text.
```

> **Why it works:** simplifies without adding new medical claims.

## 2. Clinical note structuring

```text
Convert this dictated consultation transcript into a SOAP note
(Subjective, Objective, Assessment, Plan):
"""{transcript}"""

Use only information stated in the transcript. Write "not documented" for missing sections.
List any statements that were ambiguous so the clinician can verify them.
```

> **Why it works:** "not documented" and an ambiguity list prevent invented clinical details.

## 3. Medical literature summary

```text
Summarize this study abstract for a busy clinician:
"""{abstract}"""

Give: question, design, population and size, main result with numbers,
limitations, and how strong the evidence is (and why). Max 150 words.
Do not generalize beyond the studied population.
```

> **Why it works:** structured summaries make study quality visible at a glance.

## 4. Health-data annotation guideline

```text
Write annotation guidelines for labeling {entity_types} (e.g. symptoms, medications,
dosages) in de-identified clinical notes.

Include: definitions, span boundary rules (what to include/exclude), how to handle
negation ("no fever"), abbreviations, and 3 annotated examples. Remind annotators
to report any remaining personal identifiers instead of labeling them.
```

> **Why it works:** negation and span rules are the main source of disagreement in clinical NER.

## 5. Health chatbot safety prompt

```text
You are a health information assistant for {organization}.

- Provide general, evidence-based information only; never diagnose or prescribe.
- If the user describes emergency symptoms (chest pain, difficulty breathing, stroke signs,
  suicidal thoughts), tell them to contact emergency services ({local_number}) immediately.
- Encourage consulting a doctor or pharmacist for personal decisions.
- Say "I don't know" when unsure.
```

> **Why it works:** explicit emergency routing and scope limits are essential safety guardrails.
