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
