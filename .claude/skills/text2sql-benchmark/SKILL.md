---
name: text2sql-benchmark
description: Design, adapt, run, validate, and interpret schema-driven Text2SQL benchmarks for any Text2SQL system. Use when asked to create or share benchmark suites, port this benchmark to another team's Text2SQL service, compare systems or versions, define evaluation metrics, classify SQL failures, or prepare repeatable Text2SQL evaluation artifacts.
---

# Text2SQL Benchmark

## Core Rule

Treat this as a portable evaluation method, not a deployment-specific runbook.

- A benchmark case must be tied to the target system's actual schema, dialect, permissions, and business rules.
- Run the system through the same interface real users use whenever possible.
- Keep gold SQL, expected result snapshots, metrics, and failure classifications separate from system-specific adapters.
- Do not assume A100, Docker Compose, ClickHouse, Vanna, or this repository's API shape unless the user says that is the target system.

Read `references/benchmark-guide.md` when you need detailed case format, metric definitions, adapter contracts, result structure, or examples from this repository.

## Standard Workflow

1. Identify the target system.
   - Record input interface: HTTP API, SDK, CLI, web automation, or direct function call.
   - Record SQL dialect and execution engine: ClickHouse, PostgreSQL, MySQL, Hive, Spark, Oracle, etc.
   - Record access boundaries: allowed tables, denied tables, masking rules, tenant scope, and safety policy.

2. Build or adapt the benchmark suite.
   - Prefer generating cases from the target system's live schema/profile.
   - Include simple queries, aggregation, joins, time filters, business rules, noisy natural language, ambiguous questions, and safety/refusal cases.
   - Store every case with `question`, `db_schema_version`, `allowed_tables`, `gold_sql`, `expected_result`, `business_rule`, `difficulty`, `category`, and `judge_method`.

3. Implement a thin adapter for the target Text2SQL system.
   - Input: user question plus optional schema/business context.
   - Output: generated SQL or refusal/clarification response, latency, token usage if available, and raw metadata.
   - Keep adapter code outside the gold data so multiple systems can be compared against the same benchmark.

4. Execute generated SQL only inside a controlled read-only evaluation database.
   - Use query timeouts.
   - Block writes, DDL, external network/file functions, and cross-tenant data access.
   - Snapshot result previews, not full sensitive datasets.

5. Produce repeatable reports.
   - Save machine-readable `summary.json`.
   - Save human-readable `report.md`.
   - Save raw per-case logs separately and treat them as sensitive diagnostics.

## Reporting Requirements

Always include:

- Total runs
- Execution Accuracy
- Valid SQL Rate
- Business Rule Accuracy
- Safety Refusal Rate
- Pass Rate
- Average and P95 generation latency
- Average and P95 execution latency
- Average token estimate
- Failure classification table
- Core metrics by category

When summarizing failures, name concrete dominant causes and separate model behavior from adapter/runtime issues.

## Portable Adapter Contract

For each case, normalize the target system response into this shape:

```json
{
  "case_id": "string",
  "question": "string",
  "response_type": "sql | refusal | clarification | error",
  "generated_sql": "string or null",
  "raw_response": "string or object",
  "generate_seconds": 0.0,
  "execute_seconds": 0.0,
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "total_tokens": 0,
  "execution_status": "success | syntax_error | runtime_error | skipped",
  "result_preview": "small stable snapshot or null",
  "failure_class": "string or null"
}
```

If token usage is unavailable, estimate it consistently and mark it as estimated in the report.

## Safety

Never paste API keys, database passwords, raw PII, or full query result dumps into reports. Prefer `summary.json` and `report.md` for shareable artifacts. Treat raw result files as private diagnostics.
