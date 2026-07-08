# V1.2 Schema-Driven Gold Benchmark Run Report

- Total runs: `1000`
- Execution Accuracy: `0.3706`
- Valid SQL Rate: `0.3706`
- Business Rule Accuracy: `0.7657`
- Safety Refusal Rate: `0.04`
- Pass Rate: `0.279`
- Avg Generate Seconds: `18.368`
- P95 Generate Seconds: `42.919`
- Avg Execute Seconds: `0.637`
- Avg Estimated Total Tokens: `2828.9`

## Error Classification

| Error | Count |
| --- | ---: |
| SQL 语法错误 | 529 |
| 表字段选错 | 10 |
| join 路径错误 | 36 |
| 时间条件错误 | 0 |
| 业务口径错误 | 0 |
| 聚合粒度错误 | 0 |
| 权限/安全错误 | 72 |
| 问题歧义但未反问 | 68 |
| 执行超时 | 0 |
| 结果格式错误 | 6 |

## Core Metrics By Category

| Category | Runs | Execution Accuracy | Valid SQL Rate | Business Rule Accuracy | Safety Refusal Rate | Pass Rate | Avg Gen(s) | P95 Gen(s) | Avg Exec(s) | P95 Exec(s) | Avg Tokens Est |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| aggregation | 220 | 0.1273 | 0.1273 | 0.9909 | None | 0.1273 | 12.04 | 20.97 | 0.239 | 2.886 | 2769.6 |
| ambiguous | 75 | None | None | None | None | 0.0933 | 37.152 | 60.169 | None | None | 2971.9 |
| business_rule | 150 | 0.3533 | 0.3533 | 0.9333 | None | 0.3533 | 15.912 | 29.392 | 0.245 | 0.86 | 2759.4 |
| join | 150 | 0.4067 | 0.4067 | 0.2467 | None | 0.12 | 21.912 | 41.851 | 1.663 | 4.196 | 2802.3 |
| noisy_language | 60 | 0.6833 | 0.6833 | None | None | 0.6833 | 19.789 | 35.159 | 0.529 | 3.49 | 2809.5 |
| safety | 75 | None | None | None | 0.04 | 0.04 | 17.432 | 40.777 | None | None | 3039.3 |
| simple_query | 120 | 0.8417 | 0.8417 | None | None | 0.8417 | 13.003 | 23.771 | 0.849 | 3.079 | 2711.9 |
| time | 150 | 0.2067 | 0.2067 | 0.7867 | None | 0.1867 | 21.359 | 48.952 | 0.415 | 3.061 | 2958.2 |

## Error Classification By Category

### aggregation

| Error | Count |
| --- | ---: |
| SQL 语法错误 | 192 |
| 表字段选错 | 0 |
| join 路径错误 | 0 |
| 时间条件错误 | 0 |
| 业务口径错误 | 0 |
| 聚合粒度错误 | 0 |
| 权限/安全错误 | 0 |
| 问题歧义但未反问 | 0 |
| 执行超时 | 0 |
| 结果格式错误 | 0 |

### ambiguous

| Error | Count |
| --- | ---: |
| SQL 语法错误 | 0 |
| 表字段选错 | 0 |
| join 路径错误 | 0 |
| 时间条件错误 | 0 |
| 业务口径错误 | 0 |
| 聚合粒度错误 | 0 |
| 权限/安全错误 | 0 |
| 问题歧义但未反问 | 68 |
| 执行超时 | 0 |
| 结果格式错误 | 0 |

### business_rule

| Error | Count |
| --- | ---: |
| SQL 语法错误 | 97 |
| 表字段选错 | 0 |
| join 路径错误 | 0 |
| 时间条件错误 | 0 |
| 业务口径错误 | 0 |
| 聚合粒度错误 | 0 |
| 权限/安全错误 | 0 |
| 问题歧义但未反问 | 0 |
| 执行超时 | 0 |
| 结果格式错误 | 0 |

### join

| Error | Count |
| --- | ---: |
| SQL 语法错误 | 87 |
| 表字段选错 | 7 |
| join 路径错误 | 36 |
| 时间条件错误 | 0 |
| 业务口径错误 | 0 |
| 聚合粒度错误 | 0 |
| 权限/安全错误 | 0 |
| 问题歧义但未反问 | 0 |
| 执行超时 | 0 |
| 结果格式错误 | 2 |

### noisy_language

| Error | Count |
| --- | ---: |
| SQL 语法错误 | 19 |
| 表字段选错 | 0 |
| join 路径错误 | 0 |
| 时间条件错误 | 0 |
| 业务口径错误 | 0 |
| 聚合粒度错误 | 0 |
| 权限/安全错误 | 0 |
| 问题歧义但未反问 | 0 |
| 执行超时 | 0 |
| 结果格式错误 | 0 |

### safety

| Error | Count |
| --- | ---: |
| SQL 语法错误 | 0 |
| 表字段选错 | 0 |
| join 路径错误 | 0 |
| 时间条件错误 | 0 |
| 业务口径错误 | 0 |
| 聚合粒度错误 | 0 |
| 权限/安全错误 | 72 |
| 问题歧义但未反问 | 0 |
| 执行超时 | 0 |
| 结果格式错误 | 0 |

### simple_query

| Error | Count |
| --- | ---: |
| SQL 语法错误 | 19 |
| 表字段选错 | 0 |
| join 路径错误 | 0 |
| 时间条件错误 | 0 |
| 业务口径错误 | 0 |
| 聚合粒度错误 | 0 |
| 权限/安全错误 | 0 |
| 问题歧义但未反问 | 0 |
| 执行超时 | 0 |
| 结果格式错误 | 0 |

### time

| Error | Count |
| --- | ---: |
| SQL 语法错误 | 115 |
| 表字段选错 | 3 |
| join 路径错误 | 0 |
| 时间条件错误 | 0 |
| 业务口径错误 | 0 |
| 聚合粒度错误 | 0 |
| 权限/安全错误 | 0 |
| 问题歧义但未反问 | 0 |
| 执行超时 | 0 |
| 结果格式错误 | 4 |
