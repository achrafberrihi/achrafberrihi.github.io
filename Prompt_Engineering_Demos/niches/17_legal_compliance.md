# Legal & Compliance

Prompts for document review and compliance support. Outputs need review by a qualified lawyer.

## 1. Contract clause extractor

```text
Extract the following clauses from this contract and return JSON:
parties, effective date, term and renewal, payment terms, termination conditions,
liability cap, confidentiality, governing law, dispute resolution.

For each: the exact clause text, a one-line plain-language summary, and the section number.
Use null if a clause is absent.

Contract: """{contract}"""
```

> **Why it works:** exact quotes with section numbers make every extraction verifiable.

## 2. Risk review against a playbook

```text
Review this contract against our negotiation playbook.

Playbook: {playbook_rules}   (e.g. "liability cap must be ≥ 12 months of fees")
Contract: """{contract}"""

For each playbook rule: compliant / deviation / missing, the relevant clause, the risk
level, and suggested redline wording.
```

> **Why it works:** a playbook turns subjective review into a consistent checklist.

## 3. Privacy policy gap check

```text
Check this privacy policy against {regulation} (e.g. GDPR, Morocco's Law 09-08):
"""{policy}"""

List required elements (controller identity, purposes, legal basis, retention, rights,
transfers, contact) and mark each present / incomplete / missing with the passage quoted.
```

> **Why it works:** element-by-element checking catches omissions that a read-through misses.

## 4. Plain-language summary of terms

```text
Summarize these terms of service for users in plain language:
"""{terms}"""

Max 10 bullet points: what users agree to, what the company can do, fees and renewals,
how to cancel, and anything unusual or user-unfriendly. Keep legal meaning intact.
```

> **Why it works:** surfaces the points users actually care about without changing their meaning.

## 5. Compliance checklist builder

```text
Create a compliance checklist for a {business_type} operating in {country} that {activity}
(e.g. collects customer data online and processes card payments).

Group by area (data protection, consumer law, tax, sector rules). For each item:
the requirement, the evidence needed to prove compliance, and how often to review it.
Note clearly where local legal advice is needed.
```

> **Why it works:** pairing each requirement with evidence makes the checklist auditable.
