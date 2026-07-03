# V1.1 Gold Benchmark 1000

This suite contains 1000 schema-aware Text2SQL benchmark samples.

Each case includes:

- `question`
- `db_schema_version`
- `allowed_tables`
- `gold_sql`
- `expected_result`
- `business_rule`
- `difficulty`
- `category`
- `judge_method`

Safety and ambiguous cases intentionally have `gold_sql: null` and should be
graded by refusal/clarification behavior, not SQL execution.

Sensitive result fields are redacted with stable SHA-256 prefixes when
`--execute-gold` is used.
