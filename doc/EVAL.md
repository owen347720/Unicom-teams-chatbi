# Text2SQL Evaluation Harness

## V1.0 Benchmark

V1.0 uses `scripts/run_v1_benchmark.py` to create a repeatable Text2SQL
benchmark from real ClickHouse values. The script:

- discovers seed values through the backend datasource API;
- builds benchmark questions from real communities, markets, and cities;
- calls `/api/v1/ask/generate-sql`;
- executes the generated SQL through `/api/v1/ask/execute-sql`;
- records generated SQL, pass/fail checks, latency, row count, truncation,
  estimated token usage, fallback status, and errors.

The current V1.0 suite contains `100` deterministic questions generated from
real seed values. The cases are stored in `benchmark/v1.0-100/cases.json`.

Case mix:

| Category | Count |
| --- | ---: |
| Aggregate/count | `30` |
| Detail/listing | `20` |
| Ranking/TopN | `20` |
| Mixed mobile + broadband | `30` |

Coverage:

- mobile community count and detail questions;
- broadband market count and detail questions;
- city-level mobile and broadband questions;
- TopN community/market/city/user-type/bandwidth distributions;
- mixed mobile + broadband detail and count questions for shared terms;
- deterministic checks for expected table hits, expected column hits, LIMIT,
  GROUP BY, hallucinated table/field names, executability, latency, and tokens.

Run on A100:

```bash
ssh A100BMS-2
cd /data1/text2sql/releases/amd64-verify
python3 run_v1_benchmark.py \
  --backend-url http://127.0.0.1:38000 \
  --output-dir /data1/text2sql/benchmarks/v1.0-100 \
  --repeats 1
```

Generate or refresh the case file without calling the model:

```bash
python3 scripts/run_v1_benchmark.py \
  --seed-file benchmark/v1.0-r3/seed.json \
  --output-dir benchmark/v1.0-100 \
  --cases-only
```

Copy results back locally:

```bash
scp -r A100BMS-2:/data1/text2sql/benchmarks/v1.0-r3/. benchmark/v1.0-r3/
```

## Metrics

- `pass_rate`: score >= 0.85 and generated SQL executed successfully.
- `executable_rate`: generated SQL executed successfully.
- `avg_score`: weighted deterministic score across SQL shape, table hits,
  column hits, forbidden hallucinated tokens, required LIMIT/GROUP BY, and
  executability.
- `generate_seconds_client`: client-observed SQL generation latency.
- `execute_seconds_client`: client-observed SQL execution latency.
- `prompt_tokens`, `completion_tokens`, `total_tokens`: provider usage when
  available.
- `*_tokens_est`: character-based estimate when provider usage is missing.

The current MiniMax-compatible endpoint does not return authoritative usage in
every path, so token estimates are always recorded and provider usage is
recorded when present.

## V1.0 100-Question Suite

- Directory: `benchmark/v1.0-100`
- Case file: `benchmark/v1.0-100/cases.json`
- Seed file: `benchmark/v1.0-100/seed.json`
- Case count: `100`
- Unique IDs: `100`

This suite is intended to replace the earlier 10-case smoke suite for ongoing
optimization comparisons. Running all 100 questions once is expected to take
material time because SQL generation is model-bound.

## Historical V1.0 Baseline

Baseline run:

- Directory: `benchmark/v1.0-r3`
- Runs: `30` (`10` cases x `3` repeats)
- Pass rate: `46.67%`
- Executable rate: `46.67%`
- Average score: `0.8133`
- Average generation latency: `13.407s`
- P50 generation latency: `12.417s`
- P95 generation latency: `25.074s`
- Average execution latency: `0.233s`
- P95 execution latency: `0.979s`
- Average estimated total tokens: `2961.8`

Per-case pass counts:

| Case | Passes |
| --- | ---: |
| `mobile_count_by_community` | `2/3` |
| `mobile_list_by_community` | `3/3` |
| `broadband_count_by_market` | `0/3` |
| `broadband_list_by_market` | `2/3` |
| `mixed_mobile_broadband_community` | `3/3` |
| `mobile_top_communities` | `1/3` |
| `broadband_top_markets` | `3/3` |
| `mobile_city_count` | `0/3` |
| `broadband_city_count` | `0/3` |
| `mixed_city_compare` | `0/3` |

Primary failure mode: generated SQL often uses unquoted Chinese aliases, such
as `AS 用户数量` or `ORDER BY 用户数`. ClickHouse rejects these queries through
the HTTP API with `400 Bad Request`. This is the first optimization target for
post-V1.0 prompt/SQL normalization work.
