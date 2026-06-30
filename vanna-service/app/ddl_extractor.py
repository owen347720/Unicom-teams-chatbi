"""
DDL 提取器模块
支持从 ClickHouse、PostgreSQL、MySQL 提取表结构 DDL 信息
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import re

from loguru import logger


@dataclass
class TableDDL:
    """表 DDL 数据类"""
    table_name: str
    ddl: str
    database: Optional[str] = None


class BaseDDLExtractor(ABC):
    """DDL 提取器基类"""

    def __init__(self, connection_config: Dict[str, Any]):
        """
        初始化提取器

        Args:
            connection_config: 连接配置字典
                - host: 主机地址
                - port: 端口
                - database: 数据库名
                - user: 用户名
                - password: 密码
        """
        self.config = connection_config
        self.connection = None

    @abstractmethod
    def connect(self) -> None:
        """建立数据库连接"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """关闭数据库连接"""
        pass

    @abstractmethod
    def get_tables(self) -> List[str]:
        """
        获取所有表名

        Returns:
            表名列表
        """
        pass

    @abstractmethod
    def extract_table_ddl(self, table_name: str) -> TableDDL:
        """
        提取单个表的 DDL

        Args:
            table_name: 表名

        Returns:
            TableDDL 对象
        """
        pass

    def extract_all_ddl(self) -> List[Dict[str, Any]]:
        """
        提取所有表的 DDL

        Returns:
            DDL 信息列表，每个元素包含 table_name, database, ddl
        """
        try:
            self.connect()
            tables = self.get_tables()
            result = []

            for table_name in tables:
                try:
                    table_ddl = self.extract_table_ddl(table_name)
                    result.append({
                        "table_name": table_ddl.table_name,
                        "database": table_ddl.database,
                        "ddl": table_ddl.ddl
                    })
                    logger.debug(f"Extracted DDL for table: {table_name}")
                except Exception as e:
                    logger.error(f"Failed to extract DDL for table {table_name}: {e}")
                    continue

            logger.info(f"Successfully extracted DDL for {len(result)} tables")
            return result

        except Exception as e:
            logger.error(f"Failed to extract all DDL: {e}")
            raise
        finally:
            self.disconnect()


class ClickHouseDDLExtractor(BaseDDLExtractor):
    """ClickHouse DDL 提取器"""

    def connect(self) -> None:
        """建立 ClickHouse 连接"""
        try:
            from clickhouse_driver import Client

            self.connection = Client(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 9000),
                database=self.config.get("database", "default"),
                user=self.config.get("user", "default"),
                password=self.config.get("password", ""),
            )
            logger.info("Connected to ClickHouse")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise

    def disconnect(self) -> None:
        """关闭 ClickHouse 连接"""
        if self.connection:
            self.connection = None
            logger.info("Disconnected from ClickHouse")

    def get_tables(self) -> List[str]:
        """获取所有 ClickHouse 表名"""
        try:
            result = self.connection.execute("SHOW TABLES")
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to get tables from ClickHouse: {e}")
            raise

    def extract_table_ddl(self, table_name: str) -> TableDDL:
        """提取 ClickHouse 表的 DDL"""
        try:
            result = self.connection.execute(f"SHOW CREATE TABLE `{table_name}`")
            if result and len(result) > 0:
                ddl = result[0][0]
                return TableDDL(
                    table_name=table_name,
                    ddl=ddl,
                    database=self.config.get("database", "default")
                )
            else:
                raise ValueError(f"No DDL returned for table {table_name}")
        except Exception as e:
            logger.error(f"Failed to extract DDL for {table_name}: {e}")
            raise


class PostgreSQLDDLExtractor(BaseDDLExtractor):
    """PostgreSQL DDL 提取器"""

    def connect(self) -> None:
        """建立 PostgreSQL 连接"""
        try:
            import psycopg2

            self.connection = psycopg2.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 5432),
                database=self.config.get("database", "postgres"),
                user=self.config.get("user", "postgres"),
                password=self.config.get("password", ""),
            )
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def disconnect(self) -> None:
        """关闭 PostgreSQL 连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from PostgreSQL")

    def get_tables(self) -> List[str]:
        """获取所有 PostgreSQL 表名（排除系统表）"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """)
                result = cursor.fetchall()
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to get tables from PostgreSQL: {e}")
            raise

    def extract_table_ddl(self, table_name: str) -> TableDDL:
        """提取 PostgreSQL 表的 DDL"""
        try:
            with self.connection.cursor() as cursor:
                # 尝试使用 pg_dump 风格的 DDL 生成
                ddl = self._generate_ddl(cursor, table_name)
                return TableDDL(
                    table_name=table_name,
                    ddl=ddl,
                    database=self.config.get("database", "postgres")
                )
        except Exception as e:
            logger.error(f"Failed to extract DDL for {table_name}: {e}")
            raise

    def _generate_ddl(self, cursor, table_name: str) -> str:
        """生成 PostgreSQL 表的 CREATE TABLE 语句"""
        try:
            # 获取列信息
            cursor.execute("""
                SELECT
                    column_name,
                    data_type,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))

            columns = cursor.fetchall()

            if not columns:
                raise ValueError(f"Table {table_name} not found or has no columns")

            # 获取主键信息
            cursor.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = 'public'
                AND tc.table_name = %s
                AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position
            """, (table_name,))

            primary_keys = [row[0] for row in cursor.fetchall()]

            # 获取外键信息
            cursor.execute("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                WHERE tc.table_schema = 'public'
                AND tc.table_name = %s
                AND tc.constraint_type = 'FOREIGN KEY'
            """, (table_name,))

            foreign_keys = cursor.fetchall()

            # 构建 CREATE TABLE 语句
            ddl_parts = [f"CREATE TABLE {table_name} ("]
            column_defs = []

            for col in columns:
                col_name, data_type, char_len, num_prec, num_scale, is_nullable, col_default = col

                # 构建列定义
                if data_type == "character varying" and char_len:
                    type_str = f"varchar({char_len})"
                elif data_type == "character" and char_len:
                    type_str = f"char({char_len})"
                elif data_type in ("numeric", "decimal") and num_prec:
                    if num_scale:
                        type_str = f"numeric({num_prec},{num_scale})"
                    else:
                        type_str = f"numeric({num_prec})"
                else:
                    type_str = data_type

                col_def = f"    {col_name} {type_str}"

                if col_default:
                    col_def += f" DEFAULT {col_default}"

                if is_nullable == "NO":
                    col_def += " NOT NULL"

                column_defs.append(col_def)

            # 添加主键约束
            if primary_keys:
                column_defs.append(f"    PRIMARY KEY ({', '.join(primary_keys)})")

            # 添加外键约束
            for fk in foreign_keys:
                col_name, fk_table, fk_col = fk
                column_defs.append(
                    f"    FOREIGN KEY ({col_name}) REFERENCES {fk_table}({fk_col})"
                )

            ddl_parts.append(",\n".join(column_defs))
            ddl_parts.append(");")

            return "\n".join(ddl_parts)

        except Exception as e:
            logger.error(f"Failed to generate DDL for {table_name}: {e}")
            raise


class MySQLDDLExtractor(BaseDDLExtractor):
    """MySQL DDL 提取器"""

    def connect(self) -> None:
        """建立 MySQL 连接"""
        try:
            import mysql.connector

            self.connection = mysql.connector.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 3306),
                database=self.config.get("database", ""),
                user=self.config.get("user", "root"),
                password=self.config.get("password", ""),
            )
            logger.info("Connected to MySQL")
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            raise

    def disconnect(self) -> None:
        """关闭 MySQL 连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Disconnected from MySQL")

    def get_tables(self) -> List[str]:
        """获取所有 MySQL 表名"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES")
            result = cursor.fetchall()
            cursor.close()
            return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to get tables from MySQL: {e}")
            raise

    def extract_table_ddl(self, table_name: str) -> TableDDL:
        """提取 MySQL 表的 DDL"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            result = cursor.fetchone()
            cursor.close()

            if result and len(result) >= 2:
                ddl = result[1]  # SHOW CREATE TABLE 返回 (table_name, ddl)
                return TableDDL(
                    table_name=table_name,
                    ddl=ddl,
                    database=self.config.get("database", "")
                )
            else:
                raise ValueError(f"No DDL returned for table {table_name}")
        except Exception as e:
            logger.error(f"Failed to extract DDL for {table_name}: {e}")
            raise


class DDLExtractor:
    """
    DDL 提取器统一接口

    支持数据库类型：clickhouse, postgresql, mysql

    Example:
        # ClickHouse
        extractor = DDLExtractor("clickhouse", {
            "host": "localhost",
            "port": 9000,
            "database": "default",
            "user": "default",
            "password": ""
        })

        # PostgreSQL
        extractor = DDLExtractor("postgresql", {
            "host": "localhost",
            "port": 5432,
            "database": "mydb",
            "user": "postgres",
            "password": "secret"
        })

        # MySQL
        extractor = DDLExtractor("mysql", {
            "host": "localhost",
            "port": 3306,
            "database": "mydb",
            "user": "root",
            "password": "secret"
        })

        # 提取所有 DDL
        ddl_list = extractor.extract_all_ddl()
    """

    # 数据库类型到提取器类的映射
    EXTRACTOR_MAP = {
        "clickhouse": ClickHouseDDLExtractor,
        "postgresql": PostgreSQLDDLExtractor,
        "postgres": PostgreSQLDDLExtractor,
        "mysql": MySQLDDLExtractor,
    }

    def __init__(self, db_type: str, connection_config: Dict[str, Any]):
        """
        初始化 DDL 提取器

        Args:
            db_type: 数据库类型 (clickhouse, postgresql, mysql)
            connection_config: 连接配置字典

        Raises:
            ValueError: 不支持的数据库类型
        """
        self.db_type = db_type.lower()

        if self.db_type not in self.EXTRACTOR_MAP:
            supported = ", ".join(self.EXTRACTOR_MAP.keys())
            raise ValueError(
                f"Unsupported database type: {db_type}. "
                f"Supported types: {supported}"
            )

        self.extractor = self.EXTRACTOR_MAP[self.db_type](connection_config)
        logger.info(f"Initialized DDLExtractor for {db_type}")

    def extract_all_ddl(self) -> List[Dict[str, Any]]:
        """
        提取所有表的 DDL

        Returns:
            DDL 信息列表，每个元素包含:
            - table_name: 表名
            - database: 数据库名
            - ddl: DDL 语句
        """
        return self.extractor.extract_all_ddl()

    def get_tables(self) -> List[str]:
        """
        获取所有表名

        Returns:
            表名列表
        """
        try:
            self.extractor.connect()
            tables = self.extractor.get_tables()
            self.extractor.disconnect()
            return tables
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            raise

    def extract_table_ddl(self, table_name: str) -> Dict[str, Any]:
        """
        提取单个表的 DDL

        Args:
            table_name: 表名

        Returns:
            DDL 信息字典
        """
        try:
            self.extractor.connect()
            table_ddl = self.extractor.extract_table_ddl(table_name)
            self.extractor.disconnect()
            return {
                "table_name": table_ddl.table_name,
                "database": table_ddl.database,
                "ddl": table_ddl.ddl
            }
        except Exception as e:
            logger.error(f"Failed to extract DDL for {table_name}: {e}")
            raise
