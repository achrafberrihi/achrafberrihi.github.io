# Data Engineering & SQL

Prompts for queries, pipelines and data quality.

## 1. Natural language to SQL

```text
Write a {dialect} SQL query for this request: "{question}"

Schema:
{schema_ddl}

Rules:
- Use only the tables and columns listed.
- Prefer explicit JOINs and CTEs for readability.
- If the request is ambiguous (e.g. "last month"), state your assumption in a SQL comment.
Return only the query.
```

> **Why it works:** schema grounding prevents invented columns; assumptions become visible in comments.

## 2. Query optimizer

```text
This query is slow on {row_count} rows in {database}:

{query}

Explain why it is slow (scans, missing indexes, functions on indexed columns, N+1 patterns),
propose an optimized version, and list the indexes to create. Keep results identical.
```

> **Why it works:** requiring identical results keeps the optimization safe.

## 3. Data quality rules generator

```text
Here is a sample of a dataset ({n} rows shown) and its column descriptions:

{sample_csv}
{column_descriptions}

Propose data quality checks: nulls, ranges, formats, uniqueness, referential integrity
and cross-column rules (e.g. end_date >= start_date). For each rule give the SQL or
pandas check and the expected failure rate threshold.
```

> **Why it works:** concrete, executable checks rather than generic advice.

## 4. ETL pipeline designer

```text
Design a pipeline that moves {source} data to {destination} every {frequency}.

Cover: extraction method, incremental loading strategy, schema changes, deduplication,
error handling and retries, monitoring/alerts, and backfill. Recommend tools for a
small team with a {budget} budget and explain one trade-off you made.
```

> **Why it works:** forcing a stated trade-off produces a real recommendation, not a list of options.

## 5. Messy data cleaner spec

```text
Here are 20 raw values from the "{column}" column:
{values}

1. Describe the inconsistencies (formats, typos, units, languages).
2. Write a Python function clean_{column}(value) that normalizes them.
3. List values the function cannot handle safely and should flag for review.
```

> **Why it works:** asking for unhandled cases prevents silent wrong conversions.
