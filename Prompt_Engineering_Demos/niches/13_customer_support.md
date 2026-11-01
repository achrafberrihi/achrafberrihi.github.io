# Customer Support

Prompts for support agents, ticket triage and chatbots.

## 1. Support chatbot system prompt

```text
You are the support assistant for {company}. Tone: friendly, concise, professional.

You can: answer questions using the knowledge base below, check order status with tools,
and create tickets. You cannot: give refunds, change account ownership, or promise delivery dates.
When you cannot help, say so and offer to connect a human agent.
Never invent policies. Reply in the customer's language (French, Arabic, English).

Knowledge base: """{kb}"""
```

> **Why it works:** explicit can/cannot lists define a safe scope and a clean human handoff.

## 2. Ticket triage

```text
Classify this support ticket.

Ticket: """{ticket}"""

Return JSON:
{"category": "billing|technical|delivery|account|feedback|other",
 "priority": "low|medium|high|urgent",
 "sentiment": "positive|neutral|negative|angry",
 "language": "...",
 "summary": "<one line>",
 "suggested_team": "..."}
Urgent = service down, security issue, or legal threat.
```

> **Why it works:** a defined "urgent" rule keeps priority consistent across agents.

## 3. Empathetic reply drafter

```text
Draft a reply to this customer.

Customer message: """{message}"""
Facts from our system: {facts}
What we can offer: {options}

Acknowledge the specific problem in the first sentence, explain what happened in plain words,
state the solution and timeline, and close without generic apologies.
Max 120 words. Do not promise anything not listed in "What we can offer".
```

> **Why it works:** grounding in system facts and allowed options prevents over-promising.

## 4. Knowledge-base article from resolved tickets

```text
Here are {n} resolved tickets about the same issue:
{tickets}

Write a help-center article: title phrased as the customer's question, symptoms,
cause (simple terms), step-by-step solution, and when to contact support.
Remove all personal data.
```

> **Why it works:** turns repeated tickets into self-service content and reduces volume.

## 5. Conversation quality audit

```text
Audit this support conversation between an agent and a customer:
"""{conversation}"""

Score 1–5: resolution, accuracy, empathy, efficiency, policy compliance.
Quote the moments that most affected each score and give the agent 2 specific coaching tips.
```

> **Why it works:** quoted evidence makes coaching concrete and fair.
