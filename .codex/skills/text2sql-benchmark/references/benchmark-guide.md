# Benchmark Guide

## Suites

| Suite | Role | Path |
| --- | --- | --- |
| V1.0 smoke | Historical small baseline | `benchmark/v1.0-r3` |
| V1.0 100 | Lightweight regression | `benchmark/v1.0-100` |
| V1.1 1000 | Superseded format prototype | `benchmark/v1.1-gold-1000` |
| V1.2 1000 | Current primary benchmark | `benchmark/v1.2-schema-gold-1000` |

V1.2 distribution:

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

V1.2 contains 850 executable SQL cases and 150 human-review cases for ambiguity/safety behavior.

## Key Files

- `scripts/generate_v12_schema_gold_benchmark.py`: generate V1.2 cases from live schema/profile and optionally execute gold SQL snapshots.
- `scripts/run_v11_gold_benchmark.py`: generic gold benchmark runner used for V1.2 full-system runs.
- `benchmark/schema-live`: live A100 ClickHouse schema/profile snapshot used to generate V1.2.
- `benchmark/v1.2-schema-gold-1000`: generated V1.2 gold cases and gold execution snapshots.
- `benchmark/v1.2-schema-gold-1000-run-20260703`: first full-system V1.2 benchmark run summary.

## Metric Definitions

- `Execution Accuracy`: SQL-task rate where generated SQL executed successfully.
- `Valid SQL Rate`: SQL-task rate where response looked like SQL and executed successfully.
- `Business Rule Accuracy`: rate where expected tables and coarse business shape were respected.
- `Safety Refusal Rate`: safety-task rate where the model refused or asked for authorization/desensitization instead of producing SQL.
- `Pass Rate`: overall pass rate using category-specific criteria.
- `Avg/P95 Generate Seconds`: client-observed `/generate-sql` latency.
- `Avg/P95 Execute Seconds`: client-observed SQL execution latency for generated SQL.
- `Avg Total Tokens Est`: token estimate or provider usage when available.

## Failure Classes

The runner reports these failure categories:

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

The V1.2 20260703 run had these top-level results:

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

In the V1.2 20260703 run, SQL syntax failures were mostly:

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

Primary optimization target: force ASCII aliases or quote aliases with backticks. This addresses the largest single failure source.

## Remote Commands

Health check:

```bash
ssh A100BMS-2 'curl -s http://127.0.0.1:38000/health && echo'
```

Run full benchmark:

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

Pull safe artifacts:

```bash
mkdir -p benchmark/<run-dir>
scp A100BMS-2:/data1/text2sql/benchmarks/<run-dir>/summary.json benchmark/<run-dir>/
scp A100BMS-2:/data1/text2sql/benchmarks/<run-dir>/report.md benchmark/<run-dir>/
```

## Artifact Policy

Commit:

- `summary.json`
- `report.md`

Do not commit unless explicitly requested and reviewed for sensitivity:

- `results.jsonl`
- `partial_results.jsonl`
- `results.csv`
- `run.log`

These raw files may include generated SQL, safety-test phone numbers, table identifiers, and other diagnostic details.
