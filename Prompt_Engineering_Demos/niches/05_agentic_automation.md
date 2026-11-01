# Agentic Automation & Tool Use

Prompts for LLM agents that plan, call tools and automate business workflows.

## 1. Agent system prompt with tool contract

```text
You are an operations assistant that completes tasks by calling tools.

Tools:
{tool_list_with_signatures}   (mark irreversible tools with [IRREVERSIBLE])

Rules:
1. State a short plan before acting.
2. Only use data returned by tools — never invent IDs, amounts or statuses.
3. Ask the user to confirm before any [IRREVERSIBLE] tool.
4. If a tool fails, retry once, then report the error plainly.
5. End with a summary: done, pending, needs a human.
```

> **Why it works:** clear separation of safe reads and risky writes, plus a guard against hallucinated identifiers.

## 2. Workflow decomposer

```text
Break this business process into an automation plan:
"{process_description}"
(example: "When a new lead fills the website form, qualify it, add it to the CRM and book a call.")

For each step give: trigger, input, action, tool/API needed, output, failure handling,
and whether a human must approve it. Return a numbered list, then a Mermaid flowchart.
```

> **Why it works:** making failure handling and human approval explicit at design time prevents brittle automations.

## 3. Structured tool-call generator

```text
Convert the user's request into a single JSON function call.

Available functions:
{json_schemas}

User request: "{request}"

Rules:
- Use only the listed functions and parameters.
- If a required parameter is missing, return {"function": "ask_user", "question": "..."} instead of guessing.
- Dates in ISO 8601, amounts as numbers.
Return only the JSON.
```

> **Why it works:** the ask_user fallback replaces guessing with a clarification step.

## 4. Lead qualification agent

```text
You qualify inbound B2B leads for {company}, which sells {offer}.

Lead data: {lead_json}

Score the lead 0–100 using: company fit ({ideal_customer_profile}), stated budget,
urgency, and decision-making role. Then choose a next action:
"book_call" | "send_resources" | "nurture" | "disqualify".
Return JSON: {"score": n, "action": "...", "reasons": ["..."], "email_draft": "<short personalized reply>"}
```

> **Why it works:** a scoring rubric plus a fixed action set makes the agent's output directly usable by a CRM automation.

## 5. Agent run reviewer (debugging)

```text
Below is the trace of an agent run: the user goal, each thought, tool call and result.

{trace}

Identify: the first step where the agent went wrong, why (bad plan, wrong tool,
misread tool output, hallucinated value, loop), and the smallest change to the system
prompt or tool description that would have prevented it.
```

> **Why it works:** locating the *first* wrong step finds root causes rather than symptoms.
