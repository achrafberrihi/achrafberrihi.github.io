# HR & Recruitment

Prompts for hiring, onboarding and people operations.

## 1. Job description writer

```text
Write a job description for a {role} at {company} ({team_size}, {location}/remote).

Include: mission of the role (2 sentences), 5 responsibilities with outcomes,
must-have skills (max 5), nice-to-have skills, what we offer, and the hiring process.
Use inclusive language and avoid unnecessary requirements like "10+ years" unless essential.
```

> **Why it works:** limiting must-haves widens the candidate pool without lowering the bar.

## 2. CV screening against criteria

```text
Evaluate this CV against the job criteria.

Criteria: {criteria_with_weights}
CV: """{cv}"""

For each criterion: score 0–3 with evidence quoted from the CV ("no evidence" if absent).
Give a weighted total and a recommendation (advance / maybe / reject).
Ignore name, age, gender, nationality, photo and address.
```

> **Why it works:** evidence-based scoring and ignored personal attributes reduce bias.

## 3. Structured interview guide

```text
Create a 45-minute structured interview for a {role}.

Include 6 behavioral questions ("Tell me about a time…") mapped to the competencies
{competencies}, 2 follow-up probes each, and a 1–4 scoring guide describing what a
weak and a strong answer look like.
```

> **Why it works:** same questions and anchored scoring make interviews comparable.

## 4. Onboarding plan (30-60-90 days)

```text
Write a 30-60-90 day onboarding plan for a new {role} joining {team}.

For each period: goals, key people to meet, trainings, first deliverables, and how
success is measured. Include a week-1 day-by-day schedule.
```

> **Why it works:** clear milestones reduce time-to-productivity and early turnover.

## 5. Performance review helper

```text
Help me write a fair performance review.

Employee role: {role}
Goals set: {goals}
Evidence collected (projects, feedback, metrics): {evidence}

Write: summary, achievements against each goal, strengths, development areas with
specific examples, and 2–3 goals for next period. Avoid vague praise and personality judgments.
```

> **Why it works:** tying every statement to evidence keeps reviews fair and useful.
