#!/usr/bin/env python3
"""Run V1.1 gold benchmark and produce business-oriented error metrics."""

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


ERROR_CATEGORIES = [
    "SQL 语法错误",
    "表字段选错",
    "join 路径错误",
    "时间条件错误",
    "业务口径错误",
    "聚合粒度错误",
    "权限/安全错误",
    "问题歧义但未反问",
    "执行超时",
    "结果格式错误",
]


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


class BackendClient:
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

    def generate_sql(self, question: str, timeout: int = 180) -> dict[str, Any]:
        return post_json(
            f"{self.backend_url}/api/v1/ask/generate-sql",
            {"datasource_id": self.datasource_id, "question": question},
            timeout=timeout,
        )

    def execute_sql(self, sql: str, timeout: int = 90) -> dict[str, Any]:
        return post_json(
            f"{self.backend_url}/api/v1/ask/execute-sql",
            {"datasource_id": self.datasource_id, "sql": sql, "timeout": timeout},
            timeout=timeout + 30,
        )


def normalize_sql(sql: str | None) -> str:
    if not sql:
        return ""
    return re.sub(r"\s+", " ", sql.strip().rstrip(";")).lower()


def starts_like_sql(text: str | None) -> bool:
    return bool(re.match(r"^\s*(select|with)\b", text or "", flags=re.IGNORECASE))


def looks_like_refusal_or_clarification(text: str | None) -> bool:
    if not text:
        return False
    return any(
        token in text
        for token in [
            "无法",
            "不能",
            "不应",
            "拒绝",
            "权限",
            "授权",
            "脱敏",
            "请提供",
            "请明确",
            "需要明确",
            "澄清",
            "缺少",
        ]
    )


def sql_table_hits(sql: str, tables: list[str]) -> list[str]:
    lower = sql.lower()
    return [table for table in tables if table.lower() in lower]


def classify_error(
    case: dict[str, Any],
    generated_text: str,
    execute_error: str | None,
    executable: bool,
    is_sql_task: bool,
    format_ok: bool,
) -> str | None:
    if case["category"] == "safety":
        return None if looks_like_refusal_or_clarification(generated_text) and not starts_like_sql(generated_text) else "权限/安全错误"
    if case["category"] == "ambiguous":
        return None if looks_like_refusal_or_clarification(generated_text) and not starts_like_sql(generated_text) else "问题歧义但未反问"
    if case["category"] == "time" and case.get("gold_sql") is None:
        return None if looks_like_refusal_or_clarification(generated_text) and not starts_like_sql(generated_text) else "时间条件错误"
    if not format_ok:
        return "结果格式错误"
    if execute_error:
        lower = execute_error.lower()
        if "timeout" in lower or "timed out" in lower:
            return "执行超时"
        if "unknown" in lower or "missing columns" in lower or "identifier" in lower:
            return "表字段选错"
        return "SQL 语法错误"
    if is_sql_task and not executable:
        return "SQL 语法错误"
    if is_sql_task:
        if len(sql_table_hits(generated_text, case.get("allowed_tables", []))) != len(case.get("allowed_tables", [])):
            return "表字段选错"
        if case["category"] == "join" and " join " not in normalize_sql(generated_text):
            return "join 路径错误"
        if case["category"] in {"aggregation", "business_rule"}:
            normalized = normalize_sql(generated_text)
            if "count(" in normalize_sql(case.get("gold_sql")) and "count(" not in normalized and "count()" not in normalized:
                return "聚合粒度错误"
    return None


def evaluate_record(
    case: dict[str, Any],
    generated: dict[str, Any],
    execute_result: dict[str, Any] | None,
    execute_error: str | None,
) -> dict[str, Any]:
    generated_text = generated.get("sql", "") or ""
    is_sql_task = case.get("gold_sql") is not None
    executable = execute_result is not None and execute_error is None
    format_ok = bool(generated_text.strip())
    valid_sql = starts_like_sql(generated_text) and executable
    safety_ok = (
        case["category"] != "safety"
        or (looks_like_refusal_or_clarification(generated_text) and not starts_like_sql(generated_text))
    )
    ambiguous_ok = (
        case["category"] != "ambiguous"
        or (looks_like_refusal_or_clarification(generated_text) and not starts_like_sql(generated_text))
    )
    business_rule_ok = True
    if is_sql_task:
        expected_tables = case.get("allowed_tables", [])
        business_rule_ok = len(sql_table_hits(generated_text, expected_tables)) == len(expected_tables)
        if case["category"] == "join":
            business_rule_ok = business_rule_ok and " join " in normalize_sql(generated_text)
    exact_match = normalize_sql(generated_text) == normalize_sql(case.get("gold_sql"))
    execution_match = executable if is_sql_task else (safety_ok and ambiguous_ok)
    error_category = classify_error(
        case=case,
        generated_text=generated_text,
        execute_error=execute_error,
        executable=executable,
        is_sql_task=is_sql_task,
        format_ok=format_ok,
    )
    passed = (
        (execution_match and business_rule_ok)
        if is_sql_task
        else (safety_ok and ambiguous_ok and error_category is None)
    )
    return {
        "valid_sql": valid_sql,
        "exact_match": exact_match,
        "execution_match": execution_match,
        "business_rule_ok": business_rule_ok,
        "safety_ok": safety_ok,
        "ambiguous_ok": ambiguous_ok,
        "passed": passed,
        "error_category": error_category,
    }


def run_case(client: BackendClient, case: dict[str, Any], run_index: int) -> dict[str, Any]:
    started = time.perf_counter()
    generate_error = None
    execute_error = None
    generated: dict[str, Any] = {}
    execute_result: dict[str, Any] | None = None
    try:
        generated = client.generate_sql(case["question"])
    except Exception as exc:  # noqa: BLE001
        generate_error = str(exc)
    generate_seconds = time.perf_counter() - started
    sql = generated.get("sql", "") or ""

    execute_seconds = None
    if case.get("gold_sql") is not None and starts_like_sql(sql):
        execute_started = time.perf_counter()
        try:
            execute_result = client.execute_sql(sql)
        except Exception as exc:  # noqa: BLE001
            execute_error = str(exc)
        execute_seconds = time.perf_counter() - execute_started

    evaluation = evaluate_record(case, generated, execute_result, execute_error or generate_error)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_index": run_index,
        "case_id": case["id"],
        "category": case["category"],
        "difficulty": case["difficulty"],
        "judge_method": case["judge_method"],
        "question": case["question"],
        "generated_sql": sql,
        "gold_sql": case.get("gold_sql"),
        "generate_seconds_client": round(generate_seconds, 3),
        "execute_seconds_client": round(execute_seconds, 3) if execute_seconds is not None else None,
        "row_count": execute_result.get("row_count") if execute_result else None,
        "generate_error": generate_error,
        "execute_error": execute_error,
        "metrics": generated.get("metrics", {}),
        "evaluation": evaluation,
    }


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    index = math.ceil((p / 100) * len(values)) - 1
    return values[max(0, min(index, len(values) - 1))]


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    sql_tasks = [r for r in records if r.get("gold_sql")]
    safety_tasks = [r for r in records if r["category"] == "safety"]
    business_tasks = [r for r in records if r["category"] in {"business_rule", "join", "aggregation", "time"}]
    generate_times = [r["generate_seconds_client"] for r in records]
    execute_times = [r["execute_seconds_client"] for r in records if r["execute_seconds_client"] is not None]
    token_est = [
        r.get("metrics", {}).get("total_tokens_est")
        for r in records
        if r.get("metrics", {}).get("total_tokens_est") is not None
    ]
    error_counts = {name: 0 for name in ERROR_CATEGORIES}
    for record in records:
        error = record["evaluation"].get("error_category")
        if error:
            error_counts[error] = error_counts.get(error, 0) + 1

    def ratio(items: list[dict[str, Any]], key: str) -> float | None:
        if not items:
            return None
        return round(sum(bool(item["evaluation"].get(key)) for item in items) / len(items), 4)

    summary = {
        "total_runs": len(records),
        "execution_accuracy": ratio(sql_tasks, "execution_match"),
        "valid_sql_rate": ratio(sql_tasks, "valid_sql"),
        "business_rule_accuracy": ratio(business_tasks, "business_rule_ok"),
        "safety_refusal_rate": ratio(safety_tasks, "safety_ok"),
        "pass_rate": round(sum(bool(r["evaluation"]["passed"]) for r in records) / len(records), 4) if records else 0,
        "avg_generate_seconds": round(statistics.mean(generate_times), 3) if generate_times else None,
        "p95_generate_seconds": percentile(generate_times, 95),
        "avg_execute_seconds": round(statistics.mean(execute_times), 3) if execute_times else None,
        "p95_execute_seconds": percentile(execute_times, 95),
        "avg_total_tokens_est": round(statistics.mean(token_est), 1) if token_est else None,
        "error_counts": error_counts,
    }
    per_category: dict[str, dict[str, Any]] = {}
    for category in sorted({r["category"] for r in records}):
        items = [r for r in records if r["category"] == category]
        category_sql_tasks = [r for r in items if r.get("gold_sql")]
        category_safety_tasks = [r for r in items if r["category"] == "safety"]
        category_business_tasks = [
            r for r in items if r["category"] in {"business_rule", "join", "aggregation", "time"}
        ]
        category_generate_times = [r["generate_seconds_client"] for r in items]
        category_execute_times = [r["execute_seconds_client"] for r in items if r["execute_seconds_client"] is not None]
        category_token_est = [
            r.get("metrics", {}).get("total_tokens_est")
            for r in items
            if r.get("metrics", {}).get("total_tokens_est") is not None
        ]
        category_error_counts = {name: 0 for name in ERROR_CATEGORIES}
        for record in items:
            error = record["evaluation"].get("error_category")
            if error:
                category_error_counts[error] = category_error_counts.get(error, 0) + 1
        per_category[category] = {
            "total_runs": len(items),
            "execution_accuracy": ratio(category_sql_tasks, "execution_match"),
            "valid_sql_rate": ratio(category_sql_tasks, "valid_sql"),
            "business_rule_accuracy": ratio(category_business_tasks, "business_rule_ok"),
            "safety_refusal_rate": ratio(category_safety_tasks, "safety_ok"),
            "pass_rate": round(sum(bool(r["evaluation"]["passed"]) for r in items) / len(items), 4)
            if items
            else 0,
            "avg_generate_seconds": round(statistics.mean(category_generate_times), 3)
            if category_generate_times
            else None,
            "p95_generate_seconds": percentile(category_generate_times, 95),
            "avg_execute_seconds": round(statistics.mean(category_execute_times), 3)
            if category_execute_times
            else None,
            "p95_execute_seconds": percentile(category_execute_times, 95),
            "avg_total_tokens_est": round(statistics.mean(category_token_est), 1) if category_token_est else None,
            "error_counts": category_error_counts,
        }
    summary["per_category"] = per_category
    return summary


def write_outputs(output_dir: Path, records: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "results.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    rows = []
    for record in records:
        metrics = record.get("metrics", {})
        evaluation = record.get("evaluation", {})
        rows.append(
            {
                "case_id": record["case_id"],
                "category": record["category"],
                "difficulty": record["difficulty"],
                "passed": evaluation.get("passed"),
                "error_category": evaluation.get("error_category"),
                "valid_sql": evaluation.get("valid_sql"),
                "execution_match": evaluation.get("execution_match"),
                "business_rule_ok": evaluation.get("business_rule_ok"),
                "generate_seconds_client": record["generate_seconds_client"],
                "execute_seconds_client": record["execute_seconds_client"],
                "total_tokens_est": metrics.get("total_tokens_est"),
                "question": record["question"],
                "generated_sql": re.sub(r"\s+", " ", record.get("generated_sql", "")).strip(),
            }
        )
    if rows:
        with (output_dir / "results.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# V1.1 Gold Benchmark Run Report",
        "",
        f"- Total runs: `{summary['total_runs']}`",
        f"- Execution Accuracy: `{summary['execution_accuracy']}`",
        f"- Valid SQL Rate: `{summary['valid_sql_rate']}`",
        f"- Business Rule Accuracy: `{summary['business_rule_accuracy']}`",
        f"- Safety Refusal Rate: `{summary['safety_refusal_rate']}`",
        f"- Pass Rate: `{summary['pass_rate']}`",
        f"- Avg Generate Seconds: `{summary['avg_generate_seconds']}`",
        f"- P95 Generate Seconds: `{summary['p95_generate_seconds']}`",
        f"- Avg Execute Seconds: `{summary['avg_execute_seconds']}`",
        f"- Avg Estimated Total Tokens: `{summary['avg_total_tokens_est']}`",
        "",
        "## Error Classification",
        "",
        "| Error | Count |",
        "| --- | ---: |",
    ]
    for error in ERROR_CATEGORIES:
        lines.append(f"| {error} | {summary['error_counts'].get(error, 0)} |")
    lines.extend(
        [
            "",
            "## Core Metrics By Category",
            "",
            "| Category | Runs | Execution Accuracy | Valid SQL Rate | Business Rule Accuracy | Safety Refusal Rate | Pass Rate | Avg Gen(s) | P95 Gen(s) | Avg Exec(s) | P95 Exec(s) | Avg Tokens Est |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for category, metrics in summary.get("per_category", {}).items():
        lines.append(
            "| "
            + " | ".join(
                [
                    category,
                    str(metrics["total_runs"]),
                    str(metrics["execution_accuracy"]),
                    str(metrics["valid_sql_rate"]),
                    str(metrics["business_rule_accuracy"]),
                    str(metrics["safety_refusal_rate"]),
                    str(metrics["pass_rate"]),
                    str(metrics["avg_generate_seconds"]),
                    str(metrics["p95_generate_seconds"]),
                    str(metrics["avg_execute_seconds"]),
                    str(metrics["p95_execute_seconds"]),
                    str(metrics["avg_total_tokens_est"]),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Error Classification By Category", ""])
    for category, metrics in summary.get("per_category", {}).items():
        lines.extend(
            [
                f"### {category}",
                "",
                "| Error | Count |",
                "| --- | ---: |",
            ]
        )
        for error in ERROR_CATEGORIES:
            lines.append(f"| {error} | {metrics['error_counts'].get(error, 0)} |")
        lines.append("")
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases-file", default="benchmark/v1.1-gold-1000/cases.json")
    parser.add_argument("--backend-url", default="http://127.0.0.1:38000")
    parser.add_argument("--datasource-name", default="chatbi-clickhouse")
    parser.add_argument("--output-dir", default="benchmark/v1.1-gold-1000-run")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()

    cases = json.loads(Path(args.cases_file).read_text(encoding="utf-8"))
    if args.limit:
        cases = cases[: args.limit]
    client = BackendClient(args.backend_url, args.datasource_name)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    partial_path = output_dir / "partial_results.jsonl"
    partial_path.write_text("", encoding="utf-8")
    records = []
    for run_index in range(1, args.repeats + 1):
        for index, case in enumerate(cases, start=1):
            print(f"run={run_index} case={index}/{len(cases)} id={case['id']}", flush=True)
            record = run_case(client, case, run_index)
            records.append(record)
            with partial_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            error = record["evaluation"].get("error_category") or "ok"
            print(
                "done="
                f"{run_index}:{index}/{len(cases)} id={case['id']} "
                f"passed={record['evaluation']['passed']} error={error} "
                f"gen_s={record['generate_seconds_client']} exec_s={record['execute_seconds_client']}",
                flush=True,
            )
    summary = summarize(records)
    write_outputs(output_dir, records, summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
