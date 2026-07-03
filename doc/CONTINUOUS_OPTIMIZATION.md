# Continuous Optimization Log

## Baseline: V1.0 Text2SQL

Benchmark artifacts are stored in:

- `benchmark/v1.2-schema-gold-1000`: current 1000-question gold benchmark suite generated from live A100 ClickHouse schema/profile
- `benchmark/v1.1-gold-1000`: superseded format prototype; do not use as the primary benchmark
- `benchmark/v1.0-100`: 100-question benchmark suite for ongoing optimization
- `benchmark/v1.0`: 10-run smoke baseline
- `benchmark/v1.0-r3`: 30-run baseline used for comparison

Use `benchmark/v1.2-schema-gold-1000/cases.json` as the primary benchmark
question set after gold SQL snapshots are populated.
Use `benchmark/v1.0-100/cases.json` as a lighter smoke/regression suite.
Use `benchmark/v1.0-r3/summary.json`, `results.csv`, and `results.jsonl` as the
historical baseline before prompt, schema-context, SQL-normalization, or model
changes.

Current V1.0 baseline:

- Pass rate: `46.67%`
- Executable rate: `46.67%`
- Average generation latency: `13.407s`
- P95 generation latency: `25.074s`
- Average execution latency: `0.233s`
- Average estimated total tokens: `2961.8`

## Optimization Backlog

0. Finish V1.2 schema-driven gold snapshots on A100, then run the full system
   benchmark against `benchmark/v1.2-schema-gold-1000/cases.json`.

1. Fix ClickHouse alias safety.
   Generated SQL frequently uses Chinese aliases without quoting. Add prompt
   constraints and/or SQL normalization so aliases are ASCII or wrapped in
   backticks.

2. Remove unnecessary `LIMIT` from aggregate count queries.
   Some aggregate queries include `LIMIT 100`. It usually executes when aliases
   are valid, but it is unnecessary and should be discouraged for count-only
   questions.

3. Add SQL dry-run validation and repair.
   After generation, run a cheap validation path. If ClickHouse returns syntax
   errors, apply deterministic fixes for common cases or retry with the error
   message and schema context.

4. Reduce schema prompt size.
   Average estimated total tokens are about `2961.8`. Table ranking and field
   pruning should be tightened after accuracy stabilizes.

5. Keep benchmark generation schema-driven.
   Refresh `benchmark/schema-live` from A100 before creating a new baseline, and
   fail generation if required table samples are missing.
