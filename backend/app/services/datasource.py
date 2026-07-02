# backend/app/services/datasource.py

import logging
import time
import uuid
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.datasource import Datasource
from app.services.encryption import decrypt, encrypt

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = ("clickhouse", "postgresql", "mysql")


def _question_terms(question: str) -> list[str]:
    separators = " ，。；;,.!?！？()（）[]【】/\\|:-_"
    normalized = question.lower()
    for separator in separators:
        normalized = normalized.replace(separator, " ")
    return [term for term in normalized.split() if term]


class DatasourceService:
    """数据源管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def list_datasources(self) -> list[Datasource]:
        """获取所有数据源列表（注意：返回的对象包含加密密码，API 层需脱敏）"""
        stmt = select(Datasource).order_by(Datasource.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_datasource(self, datasource_id: uuid.UUID) -> Optional[Datasource]:
        """根据 ID 获取数据源"""
        return self.db.get(Datasource, datasource_id)

    def add_datasource(
        self,
        name: str,
        type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
    ) -> Datasource:
        """
        添加数据源，测试连接后保存。
        """
        if type not in SUPPORTED_TYPES:
            raise ValueError(f"不支持的数据库类型: {type}")

        tables_count = self._test_connection_internal(
            type, host, port, username, password, database
        )

        encrypted_password = encrypt(password)
        datasource = Datasource(
            name=name,
            type=type,
            host=host,
            port=port,
            username=username,
            password=encrypted_password,
            database=database,
            tables_count=tables_count,
        )
        self.db.add(datasource)
        self.db.commit()
        self.db.refresh(datasource)
        logger.info(f"Added datasource: {name} ({type})")
        return datasource

    def update_datasource(
        self,
        datasource_id: uuid.UUID,
        name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Datasource]:
        """更新数据源配置。只更新传入的非 None 字段。"""
        datasource = self.get_datasource(datasource_id)
        if datasource is None:
            return None

        if name is not None:
            datasource.name = name
        if host is not None:
            datasource.host = host
        if port is not None:
            datasource.port = port
        if username is not None:
            datasource.username = username
        if password is not None:
            datasource.password = encrypt(password)
        if is_active is not None:
            datasource.is_active = is_active

        self.db.commit()
        self.db.refresh(datasource)
        logger.info(f"Updated datasource: {datasource_id}")
        return datasource

    def delete_datasource(self, datasource_id: uuid.UUID) -> dict:
        """
        删除数据源及其在 Vanna Service 中的训练数据。

        Returns:
            dict with success flag and training_data_removed count
        """
        datasource = self.get_datasource(datasource_id)
        if datasource is None:
            return {"success": False, "training_data_removed": 0}

        # Count training data before deletion (FK cascade or manual cleanup)
        from app.models.training import TrainingData
        from sqlalchemy import func

        count_result = (
            self.db.query(func.count(TrainingData.id))
            .filter(TrainingData.datasource_id == datasource_id)
            .scalar()
        )
        training_removed = count_result or 0

        # Delete from DB first
        self.db.delete(datasource)
        self.db.commit()

        # Then notify vanna-service (non-fatal if it fails)
        self._notify_vanna_delete(datasource_id)

        logger.info(f"Deleted datasource: {datasource_id} (training_data_removed: {training_removed})")
        return {"success": True, "training_data_removed": training_removed}

    def test_connection(self, datasource_id: uuid.UUID) -> dict:
        """测试数据源连接。"""
        datasource = self.get_datasource(datasource_id)
        if datasource is None:
            return {
                "success": False,
                "message": "Datasource not found",
                "tables_count": 0,
                "response_time": 0,
            }

        plaintext_password = decrypt(datasource.password)
        start_time = time.time()
        try:
            tables_count = self._test_connection_internal(
                datasource.type,
                datasource.host,
                datasource.port,
                datasource.username,
                plaintext_password,
                datasource.database,
            )
            elapsed = time.time() - start_time
            return {
                "success": True,
                "message": "Connection successful",
                "tables_count": tables_count,
                "response_time": round(elapsed, 3),
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "message": str(e),
                "tables_count": 0,
                "response_time": round(elapsed, 3),
            }

    def get_tables(self, datasource_id: uuid.UUID) -> list[dict]:
        """获取数据源中所有表的结构信息。"""
        datasource = self.get_datasource(datasource_id)
        if datasource is None:
            raise ValueError(f"Datasource {datasource_id} not found")

        plaintext_password = decrypt(datasource.password)
        return self._extract_tables(
            datasource.type,
            datasource.host,
            datasource.port,
            datasource.username,
            plaintext_password,
            datasource.database,
        )

    def get_table_schema(self, datasource_id: uuid.UUID, table_name: str) -> dict:
        """获取指定表的详细 schema 信息。"""
        datasource = self.get_datasource(datasource_id)
        if datasource is None:
            raise ValueError(f"Datasource {datasource_id} not found")

        plaintext_password = decrypt(datasource.password)
        return self._extract_table_schema(
            datasource.type,
            datasource.host,
            datasource.port,
            datasource.username,
            plaintext_password,
            datasource.database,
            table_name,
        )

    def build_schema_context(self, datasource: Datasource, question: str) -> str:
        """Build a compact live schema prompt for SQL generation."""
        if datasource.type != "clickhouse":
            return ""

        plaintext_password = decrypt(datasource.password)
        try:
            if self._is_clickhouse_http_port(datasource.port):
                return self._build_clickhouse_http_schema_context(
                    host=datasource.host,
                    port=datasource.port,
                    username=datasource.username,
                    password=plaintext_password,
                    database=datasource.database,
                    question=question,
                )
        except Exception as e:
            logger.warning(f"Failed to build schema context: {e}")
        return ""

    def _execute_sql_direct(
        self,
        db_type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        sql: str,
        timeout: int = 60,
        max_rows: int = 1000,
    ) -> dict:
        """
        直接执行 SQL 并返回结果。

        Returns:
            dict with columns, rows, row_count, execution_time, truncated
        """
        import time as _time

        if db_type == "mysql":
            import mysql.connector

            conn = mysql.connector.connect(
                host=host, port=port, user=username, password=password, database=database
            )
            cursor = conn.cursor()
            cursor.execute(sql)
            start = _time.time()
            raw_rows = cursor.fetchmany(max_rows)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            elapsed = _time.time() - start
            cursor.close()
            conn.close()
            return {
                "columns": columns,
                "rows": [list(row) for row in raw_rows],
                "row_count": len(raw_rows),
                "execution_time": round(elapsed, 3),
                "truncated": False,
            }

        elif db_type == "postgresql":
            import psycopg2

            conn = psycopg2.connect(
                host=host, port=port, user=username, password=password, dbname=database
            )
            cursor = conn.cursor()
            cursor.execute(sql)
            start = _time.time()
            raw_rows = cursor.fetchmany(max_rows)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            elapsed = _time.time() - start
            cursor.close()
            conn.close()
            return {
                "columns": columns,
                "rows": [list(row) for row in raw_rows],
                "row_count": len(raw_rows),
                "execution_time": round(elapsed, 3),
                "truncated": False,
            }

        elif db_type == "clickhouse":
            if self._is_clickhouse_http_port(port):
                start = _time.time()
                payload = self._clickhouse_http_query_json(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    database=database,
                    sql=sql,
                    timeout=timeout,
                )
                elapsed = _time.time() - start
                columns = [meta["name"] for meta in payload.get("meta", [])]
                rows = [
                    [row.get(column) for column in columns]
                    for row in payload.get("data", [])[:max_rows]
                ]
                return {
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "execution_time": round(elapsed, 3),
                    "truncated": len(payload.get("data", [])) > max_rows,
                }

            import clickhouse_driver

            client = clickhouse_driver.Client(
                host=host, port=port, user=username, password=password, database=database
            )
            start = _time.time()
            # Use cursor for column metadata (DB-API 2.0 compatible)
            with client.cursor() as cursor:
                cursor.execute(sql)
                raw_rows = cursor.fetchmany(max_rows)
                columns = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )
            elapsed = _time.time() - start
            return {
                "columns": columns,
                "rows": [list(row) for row in raw_rows],
                "row_count": len(raw_rows),
                "execution_time": round(elapsed, 3),
                "truncated": False,
            }

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    # ---- Internal methods ----

    def _test_connection_internal(
        self,
        db_type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
    ) -> int:
        """测试连接并返回表数量。"""
        if db_type == "mysql":
            import mysql.connector

            conn = mysql.connector.connect(
                host=host, port=port, user=username, password=password, database=database
            )
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s",
                (database,),
            )
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return count

        elif db_type == "postgresql":
            import psycopg2

            conn = psycopg2.connect(
                host=host, port=port, user=username, password=password, dbname=database
            )
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return count

        elif db_type == "clickhouse":
            if self._is_clickhouse_http_port(port):
                result = self._clickhouse_http_query_text(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    database=database,
                    sql="SELECT COUNT(*) FROM system.tables WHERE database = currentDatabase()",
                    timeout=10,
                )
                return int(result.strip())

            import clickhouse_driver

            client = clickhouse_driver.Client(
                host=host, port=port, user=username, password=password, database=database
            )
            result = client.execute(
                "SELECT COUNT(*) FROM system.tables WHERE database = currentDatabase()"
            )
            count = result[0][0]
            return count

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def _is_clickhouse_http_port(self, port: int) -> bool:
        return port in {8123, 8443, 9023}

    def _clickhouse_http_query_text(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        sql: str,
        timeout: int,
    ) -> str:
        url = f"http://{host}:{port}/"
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                url,
                params={"database": database},
                content=sql.encode("utf-8"),
                auth=(username, password),
            )
            response.raise_for_status()
            return response.text

    def _clickhouse_http_query_json(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        sql: str,
        timeout: int,
    ) -> dict:
        query = sql.rstrip().rstrip(";")
        if " format " not in f" {query.lower()} ":
            query = f"{query} FORMAT JSON"
        text = self._clickhouse_http_query_text(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            sql=query,
            timeout=timeout,
        )
        import json

        return json.loads(text)

    def _build_clickhouse_http_schema_context(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        question: str,
    ) -> str:
        payload = self._clickhouse_http_query_json(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            sql=(
                "SELECT table, name, type "
                "FROM system.columns "
                "WHERE database = currentDatabase() "
                "ORDER BY table, position"
            ),
            timeout=15,
        )

        table_columns: dict[str, list[tuple[str, str]]] = {}
        for row in payload.get("data", []):
            table = row.get("table")
            name = row.get("name")
            type_name = row.get("type")
            if table and name and type_name:
                table_columns.setdefault(table, []).append((name, type_name))

        table_hints = {
            "yw_yh_zfb_daily": (
                "移网/移动用户明细表；小区字段 RESIDENT_AREA；用户号码 SERIAL_NUMBER；"
                "用户类型 USER_TYPE_CODE；宽带运营商 BROADBAND_OPERATOR。"
            ),
            "edpi_broadband_user_daily": (
                "宽带用户明细表；宽带账号 pppoe_account；装机地址 b_install_address；"
                "用户号码 b_serial_number；联系电话 b_contact_number；小区/市场 market_name。"
            ),
            "edpi_broadband_user_backup_20260428": (
                "宽带用户备份表；字段基本同 edpi_broadband_user_daily。"
            ),
            "ods_df_4g_zero_flow": "4G 小区零流量表；小区名 sec_name。",
            "ods_df_5g_zero_flow": "5G 小区零流量表；小区名 sec_name。",
            "ods_df_wls_secconfig": "无线小区配置表；小区名 sec_name；归属区域 region_name。",
        }

        selected_tables = self._rank_tables_for_question(
            table_columns=table_columns,
            table_hints=table_hints,
            question=question,
        )[:8]

        lines = [
            "数据库类型: ClickHouse",
            f"数据库名: {database}",
            "只允许使用下面列出的真实表和真实字段；禁止编造 用户表、客户表、小区名称、业务类型 等不存在的表或字段。",
            "业务口径:",
            "- 问“移网用户/移动用户”优先使用 yw_yh_zfb_daily。",
            "- 问“宽带用户”优先使用 edpi_broadband_user_daily。",
            "- 问某小区名称时，移网表用 RESIDENT_AREA LIKE '%小区名%'，宽带表用 b_install_address 或 market_name LIKE '%小区名%'。",
            "可用表结构:",
        ]
        for table in selected_tables:
            columns = table_columns.get(table, [])
            hint = table_hints.get(table)
            lines.append(f"- {table}" + (f": {hint}" if hint else ""))
            for name, type_name in columns[:80]:
                lines.append(f"  - {name} {type_name}")
            if len(columns) > 80:
                lines.append(f"  - ... 其余 {len(columns) - 80} 个字段省略")
        return "\n".join(lines)

    def _rank_tables_for_question(
        self,
        table_columns: dict[str, list[tuple[str, str]]],
        table_hints: dict[str, str],
        question: str,
    ) -> list[str]:
        question_lower = question.lower()
        scores: dict[str, int] = {}
        for table, columns in table_columns.items():
            haystack = " ".join(
                [table, table_hints.get(table, "")]
                + [name for name, _ in columns[:120]]
            ).lower()
            score = 0
            for term in _question_terms(question_lower):
                if term in haystack:
                    score += 2
            if table in table_hints:
                score += 1
            scores[table] = score

        if any(word in question for word in ("移网", "移动", "手机", "号码")):
            scores["yw_yh_zfb_daily"] = scores.get("yw_yh_zfb_daily", 0) + 20
        if "宽带" in question:
            scores["edpi_broadband_user_daily"] = (
                scores.get("edpi_broadband_user_daily", 0) + 20
            )
        if any(word in question for word in ("小区", "汇景", "新城", "地址")):
            for table in ("yw_yh_zfb_daily", "edpi_broadband_user_daily"):
                scores[table] = scores.get(table, 0) + 8

        return sorted(
            table_columns, key=lambda table: scores.get(table, 0), reverse=True
        )

    def _extract_tables(
        self,
        db_type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
    ) -> list[dict]:
        """提取所有表结构（需要 vanna-service 集成）"""
        raise NotImplementedError("Table extraction requires vanna-service integration")

    def _extract_table_schema(
        self,
        db_type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        table_name: str,
    ) -> dict:
        """提取指定表 schema"""
        raise NotImplementedError("Table schema extraction requires vanna-service integration")

    def _notify_vanna_delete(self, datasource_id: uuid.UUID) -> None:
        """通知 Vanna Service 删除数据源相关的训练数据"""
        try:
            with httpx.Client(timeout=10) as client:
                client.post(
                    f"{settings.vanna_service_url}/train/delete",
                    json={"datasource_id": str(datasource_id)},
                )
        except Exception as e:
            logger.warning(
                f"Failed to notify vanna-service about datasource deletion: {e}"
            )
