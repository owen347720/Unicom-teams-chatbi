#!/usr/bin/env python3
"""Run the V1.0 Text2SQL benchmark against a deployed backend.

The benchmark discovers real ClickHouse values through the backend API, builds
question cases from those values, runs generate + execute, and writes JSONL,
CSV, and Markdown reports. It intentionally does not persist result rows.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FORBIDDEN_TOKENS = ["用户表", "客户表", "小区名称", "业务类型"]


def post_json(url: str, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc


def get_json(url: str, timeout: int = 60) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc


class BenchmarkClient:
    def __init__(self, backend_url: str, datasource_name: str) -> None:
        self.backend_url = backend_url.rstrip("/")
        self.datasource_name = datasource_name
        self.datasource_id = self._find_datasource_id()

    def _find_datasource_id(self) -> str:
        payload = get_json(f"{self.backend_url}/api/v1/datasources/list")
        for item in payload.get("items", []):
            if item.get("name") == self.datasource_name:
                return item["id"]
        raise RuntimeError(f"Datasource not found: {self.datasource_name}")

    def execute_sql(self, sql: str, timeout: int = 90) -> dict[str, Any]:
        return post_json(
            f"{self.backend_url}/api/v1/ask/execute-sql",
            {"datasource_id": self.datasource_id, "sql": sql, "timeout": timeout},
            timeout=timeout + 30,
        )

    def generate_sql(self, question: str, timeout: int = 180) -> dict[str, Any]:
        return post_json(
            f"{self.backend_url}/api/v1/ask/generate-sql",
            {"datasource_id": self.datasource_id, "question": question},
            timeout=timeout,
        )


def scalar_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    columns = result.get("columns", [])
    rows = result.get("rows", [])
    return [dict(zip(columns, row)) for row in rows]


def discover_seed_values(client: BenchmarkClient) -> dict[str, list[dict[str, Any]]]:
    queries = {
        "mobile_communities": """
            SELECT RESIDENT_AREA AS value, count() AS cnt
            FROM yw_yh_zfb_daily
            WHERE length(RESIDENT_AREA) > 0
            GROUP BY RESIDENT_AREA
            ORDER BY cnt DESC
            LIMIT 8
        """,
        "broadband_markets": """
            SELECT market_name AS value, count() AS cnt
            FROM edpi_broadband_user_daily
            WHERE length(market_name) > 0
            GROUP BY market_name
            ORDER BY cnt DESC
            LIMIT 8
        """,
        "mobile_cities": """
            SELECT RESIDENT_CITY AS value, count() AS cnt
            FROM yw_yh_zfb_daily
            WHERE length(RESIDENT_CITY) > 0
            GROUP BY RESIDENT_CITY
            ORDER BY cnt DESC
            LIMIT 5
        """,
        "broadband_cities": """
            SELECT city AS value, count() AS cnt
            FROM edpi_broadband_user_daily
            WHERE length(city) > 0
            GROUP BY city
            ORDER BY cnt DESC
            LIMIT 5
        """,
    }
    return {name: scalar_rows(client.execute_sql(sql)) for name, sql in queries.items()}


def first_value(seed: dict[str, list[dict[str, Any]]], key: str, index: int = 0) -> str:
    values = seed.get(key, [])
    if not values:
        raise RuntimeError(f"No seed values for {key}")
    return str(values[min(index, len(values) - 1)]["value"])


def build_cases(seed: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    mobile_a = first_value(seed, "mobile_communities", 0)
    mobile_b = first_value(seed, "mobile_communities", 1)
    broadband_a = first_value(seed, "broadband_markets", 0)
    broadband_b = first_value(seed, "broadband_markets", 1)
    mobile_city = first_value(seed, "mobile_cities", 0)
    broadband_city = first_value(seed, "broadband_cities", 0)
    shared = "汇景新城"

    return [
        {
            "id": "mobile_count_by_community",
            "category": "aggregate",
            "question": f"{mobile_a} 有多少移网用户？",
            "expected_tables": ["yw_yh_zfb_daily"],
            "expected_columns": ["RESIDENT_AREA"],
        },
        {
            "id": "mobile_list_by_community",
            "category": "detail",
            "question": f"列出 {mobile_b} 的移网用户号码，最多100条",
            "expected_tables": ["yw_yh_zfb_daily"],
            "expected_columns": ["SERIAL_NUMBER", "RESIDENT_AREA"],
            "requires_limit": True,
        },
        {
            "id": "broadband_count_by_market",
            "category": "aggregate",
            "question": f"{broadband_a} 有多少宽带用户？",
            "expected_tables": ["edpi_broadband_user_daily"],
            "expected_columns": ["market_name"],
        },
        {
            "id": "broadband_list_by_market",
            "category": "detail",
            "question": f"列出 {broadband_b} 的宽带账号和联系电话，最多100条",
            "expected_tables": ["edpi_broadband_user_daily"],
            "expected_columns": ["pppoe_account", "market_name"],
            "requires_limit": True,
        },
        {
            "id": "mixed_mobile_broadband_community",
            "category": "mixed",
            "question": f"{shared} 有哪些移网用户和宽带用户？",
            "expected_tables": ["yw_yh_zfb_daily", "edpi_broadband_user_daily"],
            "expected_columns": ["RESIDENT_AREA"],
            "requires_limit": True,
        },
        {
            "id": "mobile_top_communities",
            "category": "ranking",
            "question": "移网用户数最多的10个小区是哪些？",
            "expected_tables": ["yw_yh_zfb_daily"],
            "expected_columns": ["RESIDENT_AREA"],
            "requires_group_by": True,
            "requires_limit": True,
        },
        {
            "id": "broadband_top_markets",
            "category": "ranking",
            "question": "宽带用户数最多的10个小区或市场是哪些？",
            "expected_tables": ["edpi_broadband_user_daily"],
            "expected_columns": ["market_name"],
            "requires_group_by": True,
            "requires_limit": True,
        },
        {
            "id": "mobile_city_count",
            "category": "aggregate",
            "question": f"{mobile_city} 的移网用户数量是多少？",
            "expected_tables": ["yw_yh_zfb_daily"],
            "expected_columns": ["RESIDENT_CITY"],
        },
        {
            "id": "broadband_city_count",
            "category": "aggregate",
            "question": f"{broadband_city} 的宽带用户数量是多少？",
            "expected_tables": ["edpi_broadband_user_daily"],
            "expected_columns": ["city"],
        },
        {
            "id": "mixed_city_compare",
            "category": "mixed",
            "question": f"对比 {mobile_city} 的移网用户和宽带用户数量",
            "expected_tables": ["yw_yh_zfb_daily", "edpi_broadband_user_daily"],
            "expected_columns": ["RESIDENT_CITY", "city"],
        },
    ]


def evaluate_case(case: dict[str, Any], sql: str, execute_result: dict[str, Any] | None) -> dict[str, Any]:
    sql_lower = sql.lower()
    expected_tables = case.get("expected_tables", [])
    expected_columns = case.get("expected_columns", [])
    table_hits = [table for table in expected_tables if table.lower() in sql_lower]
    column_hits = [
        column for column in expected_columns if column.lower() in sql_lower
    ]
    forbidden_hits = [token for token in FORBIDDEN_TOKENS if token in sql]
    executable = execute_result is not None and not execute_result.get("error")
    starts_like_sql = bool(re.search(r"\b(select|with)\b", sql_lower))
    has_limit = bool(re.search(r"\blimit\s+\d+\b", sql_lower))
    has_group_by = "group by" in sql_lower

    checks = {
        "starts_like_sql": starts_like_sql,
        "executable": executable,
        "expected_tables_ok": len(table_hits) == len(expected_tables),
        "expected_columns_ok": bool(column_hits) if expected_columns else True,
        "forbidden_ok": not forbidden_hits,
        "limit_ok": has_limit if case.get("requires_limit") else True,
        "group_by_ok": has_group_by if case.get("requires_group_by") else True,
    }
    weights = {
        "starts_like_sql": 0.10,
        "executable": 0.35,
        "expected_tables_ok": 0.25,
        "expected_columns_ok": 0.10,
        "forbidden_ok": 0.10,
        "limit_ok": 0.05,
        "group_by_ok": 0.05,
    }
    score = sum(weights[name] for name, ok in checks.items() if ok)
    return {
        "checks": checks,
        "score": round(score, 3),
        "passed": score >= 0.85 and executable,
        "table_hits": table_hits,
        "column_hits": column_hits,
        "forbidden_hits": forbidden_hits,
    }


def run_case(
    client: BenchmarkClient,
    case: dict[str, Any],
    run_index: int,
    execute: bool,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    generated: dict[str, Any] = {}
    execute_result: dict[str, Any] | None = None
    generate_error = None
    execute_error = None
    execute_seconds = None

    try:
        generated = client.generate_sql(case["question"])
    except Exception as exc:  # noqa: BLE001 - benchmark records failures
        generate_error = str(exc)

    generate_seconds = time.perf_counter() - started_at
    sql = generated.get("sql", "")

    if sql and execute:
        execute_started_at = time.perf_counter()
        try:
            execute_result = client.execute_sql(sql)
        except Exception as exc:  # noqa: BLE001 - benchmark records failures
            execute_error = str(exc)
            execute_result = {"error": execute_error}
        execute_seconds = time.perf_counter() - execute_started_at

    evaluation = evaluate_case(case, sql, execute_result)
    metrics = generated.get("metrics", {})
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_index": run_index,
        "case_id": case["id"],
        "category": case["category"],
        "question": case["question"],
        "generated_sql": sql,
        "confidence": generated.get("confidence"),
        "generate_seconds_client": round(generate_seconds, 3),
        "execute_seconds_client": round(execute_seconds, 3)
        if execute_seconds is not None
        else None,
        "row_count": execute_result.get("row_count") if execute_result else None,
        "columns": execute_result.get("columns") if execute_result else None,
        "truncated": execute_result.get("truncated") if execute_result else None,
        "generate_error": generate_error,
        "execute_error": execute_error,
        "metrics": metrics,
        "evaluation": evaluation,
    }


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    index = math.ceil((p / 100) * len(values)) - 1
    return values[max(0, min(index, len(values) - 1))]


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    generate_times = [r["generate_seconds_client"] for r in records]
    execute_times = [
        r["execute_seconds_client"]
        for r in records
        if r["execute_seconds_client"] is not None
    ]
    passed = [r for r in records if r["evaluation"]["passed"]]
    executable = [r for r in records if r["evaluation"]["checks"]["executable"]]
    scores = [r["evaluation"]["score"] for r in records]
    total_tokens_est = [
        r.get("metrics", {}).get("total_tokens_est")
        for r in records
        if r.get("metrics", {}).get("total_tokens_est") is not None
    ]
    return {
        "total_runs": len(records),
        "passed_runs": len(passed),
        "pass_rate": round(len(passed) / len(records), 4) if records else 0,
        "executable_runs": len(executable),
        "executable_rate": round(len(executable) / len(records), 4)
        if records
        else 0,
        "avg_score": round(statistics.mean(scores), 4) if scores else None,
        "avg_generate_seconds": round(statistics.mean(generate_times), 3)
        if generate_times
        else None,
        "p50_generate_seconds": percentile(generate_times, 50),
        "p95_generate_seconds": percentile(generate_times, 95),
        "avg_execute_seconds": round(statistics.mean(execute_times), 3)
        if execute_times
        else None,
        "p95_execute_seconds": percentile(execute_times, 95),
        "avg_total_tokens_est": round(statistics.mean(total_tokens_est), 1)
        if total_tokens_est
        else None,
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    metrics = record.get("metrics", {})
    evaluation = record.get("evaluation", {})
    checks = evaluation.get("checks", {})
    return {
        "timestamp": record["timestamp"],
        "run_index": record["run_index"],
        "case_id": record["case_id"],
        "category": record["category"],
        "question": record["question"],
        "passed": evaluation.get("passed"),
        "score": evaluation.get("score"),
        "executable": checks.get("executable"),
        "generate_seconds_client": record["generate_seconds_client"],
        "execute_seconds_client": record["execute_seconds_client"],
        "generation_seconds_server": metrics.get("generation_seconds"),
        "llm_seconds": metrics.get("llm_seconds"),
        "prompt_tokens": metrics.get("prompt_tokens"),
        "completion_tokens": metrics.get("completion_tokens"),
        "total_tokens": metrics.get("total_tokens"),
        "prompt_tokens_est": metrics.get("prompt_tokens_est"),
        "completion_tokens_est": metrics.get("completion_tokens_est"),
        "total_tokens_est": metrics.get("total_tokens_est"),
        "schema_context_tokens_est": metrics.get("schema_context_tokens_est"),
        "fallback_used": metrics.get("fallback_used"),
        "row_count": record.get("row_count"),
        "truncated": record.get("truncated"),
        "forbidden_hits": "|".join(evaluation.get("forbidden_hits", [])),
        "table_hits": "|".join(evaluation.get("table_hits", [])),
        "column_hits": "|".join(evaluation.get("column_hits", [])),
        "generate_error": record.get("generate_error"),
        "execute_error": record.get("execute_error"),
        "generated_sql": re.sub(r"\s+", " ", record.get("generated_sql", "")).strip(),
    }


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    rows = [flatten_record(record) for record in records]
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    path: Path,
    summary: dict[str, Any],
    seed: dict[str, list[dict[str, Any]]],
    cases: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> None:
    failed = [record for record in records if not record["evaluation"]["passed"]]
    lines = [
        "# Text2SQL V1.0 Benchmark Report",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Total runs: `{summary['total_runs']}`",
        f"- Pass rate: `{summary['pass_rate']:.2%}`",
        f"- Executable rate: `{summary['executable_rate']:.2%}`",
        f"- Average score: `{summary['avg_score']}`",
        f"- Average generate seconds: `{summary['avg_generate_seconds']}`",
        f"- P95 generate seconds: `{summary['p95_generate_seconds']}`",
        f"- Average execute seconds: `{summary['avg_execute_seconds']}`",
        f"- P95 execute seconds: `{summary['p95_execute_seconds']}`",
        f"- Average estimated total tokens: `{summary['avg_total_tokens_est']}`",
        "",
        "## Seed Data",
        "",
    ]
    for name, values in seed.items():
        rendered = ", ".join(f"{item['value']}({item.get('cnt')})" for item in values[:5])
        lines.append(f"- `{name}`: {rendered}")

    lines.extend(["", "## Cases", ""])
    for case in cases:
        lines.append(f"- `{case['id']}` [{case['category']}]: {case['question']}")

    lines.extend(["", "## Failed Runs", ""])
    if failed:
        for record in failed:
            lines.append(
                f"- `{record['case_id']}` run {record['run_index']}: "
                f"score={record['evaluation']['score']}, "
                f"generate_error={record.get('generate_error')}, "
                f"execute_error={record.get('execute_error')}"
            )
    else:
        lines.append("- None")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-url", default="http://127.0.0.1:38000")
    parser.add_argument("--datasource-name", default="chatbi-clickhouse")
    parser.add_argument("--output-dir", default="benchmark/v1.0")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--no-execute", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = BenchmarkClient(args.backend_url, args.datasource_name)
    seed = discover_seed_values(client)
    cases = build_cases(seed)

    records: list[dict[str, Any]] = []
    for run_index in range(1, args.repeats + 1):
        for case in cases:
            print(f"run={run_index} case={case['id']} question={case['question']}")
            records.append(
                run_case(
                    client=client,
                    case=case,
                    run_index=run_index,
                    execute=not args.no_execute,
                )
            )

    summary = summarize(records)
    write_jsonl(output_dir / "results.jsonl", records)
    write_csv(output_dir / "results.csv", records)
    (output_dir / "seed.json").write_text(
        json.dumps(seed, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "cases.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(output_dir / "report.md", summary, seed, cases, records)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
