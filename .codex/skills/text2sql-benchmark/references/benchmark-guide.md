# Benchmark Guide

## Purpose

This guide describes a portable Text2SQL benchmark process. It can evaluate this repository's deployed system, but it is not limited to A100, ClickHouse, Vanna, Docker Compose, or any specific API shape.

Use the repository's V1.2 suite as a reference implementation and seed dataset. For another Text2SQL system, first adapt the suite to that system's schema, SQL dialect, permissions, and business rules.

## Case Schema

Each benchmark case should use this shape:

```json
{
  "id": "v1.2-0001",
  "question": "用户问题",
  "db_schema_version": "schema snapshot id or date",
  "allowed_tables": ["table_a", "table_b"],
  "gold_sql": "SELECT ...",
  "expected_result": {
    "row_count": 0,
    "preview": [],
    "checksum": "optional stable checksum"
  },
  "business_rule": "口径说明",
  "difficulty": "easy | medium | hard",
  "category": "simple_query | aggregation | join | time | business_rule | noisy_language | ambiguous | safety",
  "judge_method": "exact_match | execution_match | human_review"
}
```

For ambiguity and safety cases, `gold_sql` may be null. Judge the response as clarification/refusal instead of execution.

## Portable Adapter Contract

Write one adapter per target Text2SQL system. The adapter may call an HTTP API, SDK, CLI, browser workflow, or direct function. Normalize every response to:

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
  "token_source": "provider | estimator | unavailable",
  "execution_status": "success | syntax_error | runtime_error | skipped",
  "result_preview": "small stable snapshot or null",
  "failure_class": "string or null"
}
```

Adapter requirements:

- Measure generation latency around the user-facing Text2SQL call.
- Preserve raw response privately for debugging.
- Extract only the SQL that would be executed, if any.
- Record refusal or clarification separately from SQL generation failure.
- Avoid putting credentials in logs.
- Use a read-only execution connection when executing generated SQL.

## Suite Design

Recommended 1000-case distribution:

| Category | Count | Purpose |
| --- | ---: | --- |
| simple_query | 120 | Field selection, filters, top-N, basic lookup |
| aggregation | 220 | Count, distinct, group by, ratios, ranking |
| join | 150 | Multi-table path choice and relationship correctness |
| time | 150 | Date windows, month/week/day grain, latest period |
| business_rule | 150 | Domain-specific metrics and denominator rules |
| noisy_language | 60 | Spoken language, typos, near-matches, informal phrasing |
| ambiguous | 75 | Should ask a follow-up question |
| safety | 75 | Should refuse, mask, or request authorization |

For a new business domain, regenerate questions from live schema and value profiles. Do not reuse telecom-specific questions against an unrelated schema unless the same tables and semantics exist.

## Repository Example Suites

| Suite | Role | Path |
| --- | --- | --- |
| V1.0 smoke | Historical small baseline | `benchmark/v1.0-r3` |
| V1.0 100 | Lightweight regression | `benchmark/v1.0-100` |
| V1.1 1000 | Superseded format prototype | `benchmark/v1.1-gold-1000` |
| V1.2 1000 | Current primary benchmark | `benchmark/v1.2-schema-gold-1000` |

This repository's V1.2 distribution:

| Category | Count |
| --- | ---: |
| simple_query | 120 |
| aggregation | 220 |
| join | 150 |
| time | 150 |
| business_rule | 150 |
| noisy_language | 60 |
| ambiguous | 75 |
| safety | 75 |

The repository V1.2 suite contains 850 executable SQL cases and 150 human-review cases for ambiguity/safety behavior.

## Repository Example Files

- `scripts/generate_v12_schema_gold_benchmark.py`: generate V1.2 cases from live schema/profile and optionally execute gold SQL snapshots.
- `scripts/run_v11_gold_benchmark.py`: generic gold benchmark runner used for V1.2 full-system runs.
- `benchmark/schema-live`: live A100 ClickHouse schema/profile snapshot used to generate V1.2.
- `benchmark/v1.2-schema-gold-1000`: generated V1.2 gold cases and gold execution snapshots.
- `benchmark/v1.2-schema-gold-1000-run-20260703`: first full-system V1.2 benchmark run summary.

Treat these paths as an implementation example. Other teams should replace them with their own schema snapshot, suite path, adapter, and output directory.

## Metric Definitions

- `Execution Accuracy`: SQL-task rate where generated SQL executed successfully.
- `Valid SQL Rate`: SQL-task rate where response looked like SQL and executed successfully.
- `Business Rule Accuracy`: rate where expected tables and coarse business shape were respected.
- `Safety Refusal Rate`: safety-task rate where the model refused or asked for authorization/desensitization instead of producing SQL.
- `Pass Rate`: overall pass rate using category-specific criteria.
- `Avg/P95 Generate Seconds`: client-observed Text2SQL generation latency.
- `Avg/P95 Execute Seconds`: client-observed SQL execution latency for generated SQL.
- `Avg Total Tokens Est`: token estimate or provider usage when available.

For cross-system comparison, report both overall metrics and metrics by category/difficulty. Also report token source: provider-reported, estimated, or unavailable.

## Failure Classes

Use these standard failure categories across systems:

- SQL 语法错误
- 表字段选错
- join 路径错误
- 时间条件错误
- 业务口径错误
- 聚合粒度错误
- 权限/安全错误
- 问题歧义但未反问
- 执行超时
- 结果格式错误

Classify a case by the first dominant reason it failed. If the adapter failed before the model produced a response, mark the case as runtime/adapter error in notes and do not mislabel it as model SQL failure.

## Shareable Artifacts

Share:

- Benchmark case file with sanitized questions and gold SQL.
- Schema version or schema snapshot used to create the suite.
- Adapter interface documentation.
- `summary.json` with metrics and failure counts.
- `report.md` with human-readable interpretation.

Keep private unless explicitly sanitized:

- Raw model responses.
- Full query result dumps.
- Credentials, endpoint URLs, tenant identifiers, phone numbers, addresses, or other PII.
- Provider request/response logs.

## Example Result From This Repository

The repository V1.2 20260703 run had these top-level results:

| Metric | Value |
| --- | ---: |
| Total runs | 1000 |
| Execution Accuracy | 0.3706 |
| Valid SQL Rate | 0.3706 |
| Business Rule Accuracy | 0.7657 |
| Safety Refusal Rate | 0.04 |
| Pass Rate | 0.279 |
| Avg Generate Seconds | 18.368 |
| P95 Generate Seconds | 42.919 |
| Avg Execute Seconds | 0.637 |
| Avg Total Tokens Est | 2828.9 |

Top failures:

| Failure | Count |
| --- | ---: |
| SQL 语法错误 | 529 |
| 权限/安全错误 | 72 |
| 问题歧义但未反问 | 68 |
| join 路径错误 | 36 |
| 表字段选错 | 10 |
| 结果格式错误 | 6 |

## Known Dominant SQL Syntax Causes

In the repository V1.2 20260703 run, SQL syntax failures were mostly:

| Cause | Count |
| --- | ---: |
| 中文别名未加反引号 | 369 |
| 其他 ClickHouse 执行错误 | 59 |
| 返回解释/报错文本而不是 SQL | 36 |
| KPI 表误用不存在字段 `city` | 18 |
| 无线配置表误用不存在字段 `region_name/city` | 17 |
| 带 `chatbi.` 库名前缀或字段组合导致 HTTP 错误 | 14 |
| `ORDER BY` 引用中文别名未加反引号 | 13 |
| `UNION ALL` 列/类型/字段不兼容 | 3 |

For this repository's ClickHouse setup, the primary optimization target was forcing ASCII aliases or quoting aliases with backticks. Do not assume that this is the dominant issue for other SQL dialects.

## Example Remote Commands For This Repository

These commands are examples only. Do not use them for another team's system unless it has the same host, paths, services, and API shape.

Health check example:

```bash
ssh A100BMS-2 'curl -s http://127.0.0.1:38000/health && echo'
```

Run full benchmark example:

```bash
ssh A100BMS-2 '
cd /data1/text2sql/releases/amd64-verify &&
OUT=/data1/text2sql/benchmarks/v1.2-schema-gold-1000-run-$(date +%Y%m%d-%H%M%S) &&
mkdir -p "$OUT" &&
nohup python3 -u run_v11_gold_benchmark.py \
  --cases-file /data1/text2sql/benchmarks/v1.2-schema-gold-1000/cases.json \
  --backend-url http://127.0.0.1:38000 \
  --output-dir "$OUT" > "$OUT/run.log" 2>&1 &
echo "$OUT"
'
```

Monitor:

```bash
ssh A100BMS-2 'tail -n 40 /data1/text2sql/benchmarks/<run-dir>/run.log'
ssh A100BMS-2 'wc -l /data1/text2sql/benchmarks/<run-dir>/partial_results.jsonl'
```

Pull safe artifacts example:

```bash
mkdir -p benchmark/<run-dir>
scp A100BMS-2:/data1/text2sql/benchmarks/<run-dir>/summary.json benchmark/<run-dir>/
scp A100BMS-2:/data1/text2sql/benchmarks/<run-dir>/report.md benchmark/<run-dir>/
```

## Artifact Policy

Safe to share or archive after review:

- `summary.json`
- `report.md`

Do not share unless explicitly requested and reviewed for sensitivity:

- `results.jsonl`
- `partial_results.jsonl`
- `results.csv`
- `run.log`

These raw files may include generated SQL, safety-test phone numbers, table identifiers, and other diagnostic details.
