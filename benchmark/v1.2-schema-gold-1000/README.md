# V1.2 Schema-Driven Gold Benchmark

Generated from `benchmark/schema-live` actual A100 ClickHouse schema/profile.

- Case count: `1000`
- Gold SQL cases: `850`
- Human-review cases: `150`
- Gold execution status: `850 ok`, `0 errors`
- Gold execution latency: avg `1.402s`, p50 `0.295s`, p95 `5.975s`, max `8.828s`

Files:

- `cases.json`: benchmark cases with executed gold snapshots.
- `summary.json`: category/status summary.
- `schema.json`: table/column schema snapshot.
- `profile.json`: sanitized schema profile used for generation.
- `gold_execute.log`: A100 gold execution log.

`benchmark/v1.1-gold-1000` is superseded and should not be used as the primary benchmark.
