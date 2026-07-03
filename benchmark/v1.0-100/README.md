# V1.0 100-Question Benchmark Suite

This directory contains the deterministic 100-question Text2SQL benchmark suite.

Files:

- `cases.json`: 100 benchmark questions and deterministic grading expectations.
- `seed.json`: real ClickHouse seed values used to fill the questions.

Case mix:

- Aggregate/count: 30
- Detail/listing: 20
- Ranking/TopN: 20
- Mixed mobile + broadband: 30

Run on A100:

```bash
cd /data1/text2sql/releases/amd64-verify
python3 run_v1_benchmark.py \
  --backend-url http://127.0.0.1:38000 \
  --output-dir /data1/text2sql/benchmarks/v1.0-100 \
  --repeats 1
```

For case review only, without model calls:

```bash
python3 scripts/run_v1_benchmark.py \
  --seed-file benchmark/v1.0-r3/seed.json \
  --output-dir benchmark/v1.0-100 \
  --cases-only
```
