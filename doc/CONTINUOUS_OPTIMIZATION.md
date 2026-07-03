# Continuous Optimization Log

## Baseline: V1.0 Text2SQL

Benchmark artifacts are stored in:

- `benchmark/v1.1-gold-1000`: 1000-question gold benchmark suite for business evaluation
- `benchmark/v1.0-100`: 100-question benchmark suite for ongoing optimization
- `benchmark/v1.0`: 10-run smoke baseline
- `benchmark/v1.0-r3`: 30-run baseline used for comparison

Use `benchmark/v1.1-gold-1000/cases.json` as the primary benchmark question set.
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

0. Execute V1.1 gold snapshots and full system run after A100 SSH/HTTP access is
   restored. The suite is generated locally, but `expected_result` is currently
   pending for SQL cases.

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

5. Expand benchmark coverage.
   Add more cases for date filters, zero-flow tables, network KPI tables,
   ambiguous community names, and no-answer questions.
