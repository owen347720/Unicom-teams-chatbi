---
name: text2sql-benchmark
description: Run, refresh, validate, and interpret this repository's schema-driven Text2SQL benchmark. Use when asked to run benchmark/eval/regression tests, explain V1.0/V1.1/V1.2 benchmark results, compare Text2SQL accuracy before and after optimization, produce failure classification tables, or prepare benchmark artifacts for other teams.
---

# Text2SQL Benchmark

## Core Rule

Use V1.2 as the primary benchmark unless the user explicitly asks for historical V1.0/V1.1.

- Primary suite: `benchmark/v1.2-schema-gold-1000/cases.json`
- Gold SQL status: `850/850` SQL cases executed successfully on A100.
- Current full run report: `benchmark/v1.2-schema-gold-1000-run-20260703/report.md`
- Current full run summary: `benchmark/v1.2-schema-gold-1000-run-20260703/summary.json`
- Historical V1.1 is superseded; do not present it as the main baseline.

Read `references/benchmark-guide.md` when you need detailed metric definitions, commands, result locations, or troubleshooting notes.

## Standard Workflow

1. Confirm the target suite and output directory.
   - Default suite: `benchmark/v1.2-schema-gold-1000/cases.json`
   - Default remote output pattern: `/data1/text2sql/benchmarks/v1.2-schema-gold-1000-run-YYYYMMDD`

2. If running on A100, verify services first:

```bash
ssh A100BMS-2 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep text2sql'
```

3. Run the benchmark through the backend API, not directly against ClickHouse:

```bash
ssh A100BMS-2 '
cd /data1/text2sql/releases/amd64-verify &&
python3 -u run_v11_gold_benchmark.py \
  --cases-file /data1/text2sql/benchmarks/v1.2-schema-gold-1000/cases.json \
  --backend-url http://127.0.0.1:38000 \
  --output-dir /data1/text2sql/benchmarks/v1.2-schema-gold-1000-run-YYYYMMDD
'
```

For long runs, use `nohup` and monitor `run.log` plus `partial_results.jsonl`.

4. Pull back only safe summary artifacts unless the user explicitly needs raw per-case files:

```bash
scp A100BMS-2:/data1/text2sql/benchmarks/v1.2-schema-gold-1000-run-YYYYMMDD/summary.json benchmark/v1.2-schema-gold-1000-run-YYYYMMDD/
scp A100BMS-2:/data1/text2sql/benchmarks/v1.2-schema-gold-1000-run-YYYYMMDD/report.md benchmark/v1.2-schema-gold-1000-run-YYYYMMDD/
```

Do not commit `results.jsonl`, `partial_results.jsonl`, `results.csv`, or `run.log`; they may contain generated SQL with sensitive test prompts or identifiers.

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

When summarizing failures, name concrete dominant causes. For the 20260703 V1.2 run, the main cause was SQL syntax failure, especially unquoted Chinese aliases.

## Safety

Never paste API keys, ClickHouse passwords, or raw PII into reports. Prefer `summary.json` and `report.md` for committed artifacts. Treat raw result files as local/private diagnostic artifacts.
