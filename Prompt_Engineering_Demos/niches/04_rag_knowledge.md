# RAG & Knowledge Assistants

Prompts for retrieval-augmented answers, chunking and retrieval quality.

## 1. Grounded answer with citations

```text
Answer using ONLY the numbered sources. Cite every sentence like [1] or [2][3].
If the sources don't contain the answer, reply exactly:
"The provided sources don't answer this question."

Sources:
{numbered_passages}

Question: {question}
```

> **Why it works:** citations make answers auditable; a fixed abstention string is easy to detect.

## 2. Query rewriter for retrieval

```text
Rewrite the user's question into 3 search queries for a document search engine.

Conversation so far: """{history}"""
Latest question: "{question}"

Rules:
- Resolve pronouns using the conversation ("it" → the product name).
- Query 1: keyword style. Query 2: natural question. Query 3: synonyms / alternative terms.
- Keep company-specific terms exactly as written.
Return JSON: {"queries": ["...", "...", "..."]}
```

> **Why it works:** multiple phrasings increase recall; resolving pronouns fixes follow-up questions.

## 3. Retrieval relevance grader

```text
Question: "{question}"
Retrieved passage: """{passage}"""

Rate the passage:
- 2 = directly answers the question
- 1 = related, gives partial context
- 0 = irrelevant
Return JSON: {"score": n, "reason": "<one sentence>"}
```

> **Why it works:** a 3-point scale is reliable enough to compute precision@k for the retriever.

## 4. Knowledge-base chunk enricher

```text
Here is a chunk from a {document_type} titled "{doc_title}", section "{section}":
"""{chunk}"""

Write:
1. A one-sentence context line that situates this chunk in the document (to prepend before embedding).
2. 3 questions this chunk can answer.
3. Key entities (products, dates, numbers) as a list.
Return JSON.
```

> **Why it works:** contextualized chunks and synthetic questions noticeably improve retrieval hit rates.

## 5. FAQ builder from documentation

```text
From the documentation below, build an FAQ of the 10 questions customers are most likely to ask.

Documentation: """{docs}"""

For each: the question in the customer's words, a 2–4 sentence answer using only the docs,
and the section it comes from. Flag any question the docs answer ambiguously.
```

> **Why it works:** customer phrasing differs from documentation phrasing; the FAQ bridges that gap.
