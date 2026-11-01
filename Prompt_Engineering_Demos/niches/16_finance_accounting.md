# Finance & Accounting

Prompts for analysis, reporting and finance operations. Not personalized investment advice.

## 1. Financial statement analysis

```text
Analyze these financial statements for {company} ({period}):
{income_statement}
{balance_sheet}

Compute: gross margin, operating margin, net margin, current ratio, debt-to-equity,
and revenue growth. Show each formula. Then give 3 strengths, 3 risks, and the
questions an analyst should ask management. Use only the numbers provided.
```

> **Why it works:** formulas shown make every figure auditable.

## 2. Invoice data extraction

```text
Extract fields from this invoice and return only JSON:
{"vendor": string|null, "invoice_number": string|null, "date": "YYYY-MM-DD"|null,
 "total": number|null, "tax": number|null, "currency": "ISO 4217"|null}
Use null for anything not explicitly present. Never infer values.

Invoice: """{text}"""
```

> **Why it works:** null-when-absent is the main defense against hallucinated amounts.

## 3. Expense categorization

```text
Categorize each transaction into the chart of accounts below.

Chart of accounts: {accounts}
Transactions: {transactions_csv}

Return CSV with: date, description, amount, account, confidence (high/medium/low).
Mark low confidence when the description is ambiguous and explain why in a notes column.
```

> **Why it works:** confidence levels route ambiguous items to an accountant.

## 4. Budget variance commentary

```text
Here is budget vs actual for {department}, {month}:
{table}

Write management commentary: overall variance, the 3 largest variances with likely
explanations (mark them as hypotheses), and recommended actions. Max 200 words, no jargon.
```

> **Why it works:** labeling explanations as hypotheses keeps the commentary honest.

## 5. Cash-flow forecast assumptions

```text
Build a 12-month cash-flow forecast structure for a {business_type} with:
starting cash {cash}, monthly revenue {revenue} growing {growth}%, costs {costs}.

List all assumptions explicitly, show the monthly table, and run two scenarios
(pessimistic: -20% revenue; optimistic: +15%). Highlight the month cash drops below {threshold}, if any.
```

> **Why it works:** explicit assumptions and scenarios make the forecast easy to challenge.
