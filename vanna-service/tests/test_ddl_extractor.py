"""
DDLExtractor 测试模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from app.ddl_extractor import (
    DDLExtractor,
    ClickHouseDDLExtractor,
    PostgreSQLDDLExtractor,
    MySQLDDLExtractor,
    TableDDL,
    BaseDDLExtractor,
)


class TestDDLExtractor:
    """DDLExtractor 统一接口测试"""

    def test_init_clickhouse(self):
        """测试 ClickHouse 提取器初始化"""
        config = {
            "host": "localhost",
            "port": 9000,
            "database": "default",
            "user": "default",
            "password": ""
        }
        extractor = DDLExtractor("clickhouse", config)
        assert extractor.db_type == "clickhouse"
        assert isinstance(extractor.extractor, ClickHouseDDLExtractor)

    def test_init_postgresql(self):
        """测试 PostgreSQL 提取器初始化"""
        config = {
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "user": "postgres",
            "password": "secret"
        }
        extractor = DDLExtractor("postgresql", config)
        assert extractor.db_type == "postgresql"
        assert isinstance(extractor.extractor, PostgreSQLDDLExtractor)

    def test_init_mysql(self):
        """测试 MySQL 提取器初始化"""
        config = {
            "host": "localhost",
            "port": 3306,
            "database": "testdb",
            "user": "root",
            "password": "secret"
        }
        extractor = DDLExtractor("mysql", config)
        assert extractor.db_type == "mysql"
        assert isinstance(extractor.extractor, MySQLDDLExtractor)

    def test_init_postgres_alias(self):
        """测试 PostgreSQL 别名支持"""
        config = {"host": "localhost", "port": 5432, "database": "testdb", "user": "postgres", "password": ""}
        extractor = DDLExtractor("postgres", config)  # 使用 postgres 别名
        assert extractor.db_type == "postgres"
        assert isinstance(extractor.extractor, PostgreSQLDDLExtractor)

    def test_init_unsupported_db(self):
        """测试不支持的数据库类型"""
        with pytest.raises(ValueError) as exc_info:
            DDLExtractor("oracle", {})
        assert "Unsupported database type" in str(exc_info.value)
        assert "clickhouse, postgresql, postgres, mysql" in str(exc_info.value)

    def test_init_case_insensitive(self):
        """测试数据库类型大小写不敏感"""
        config = {"host": "localhost", "port": 9000, "database": "default", "user": "default", "password": ""}
        extractor = DDLExtractor("CLICKHOUSE", config)
        assert extractor.db_type == "clickhouse"


class TestClickHouseDDLExtractor:
    """ClickHouse DDL 提取器测试"""

    @pytest.fixture
    def config(self):
        return {
            "host": "localhost",
            "port": 9000,
            "database": "testdb",
            "user": "default",
            "password": ""
        }

    @pytest.fixture
    def extractor(self, config):
        return ClickHouseDDLExtractor(config)

    def test_init(self, extractor, config):
        """测试初始化"""
        assert extractor.config == config
        assert extractor.connection is None

    def test_get_tables_mocked(self, extractor):
        """测试获取表列表 (mock)"""
        mock_client = Mock()
        mock_client.execute.return_value = [["users"], ["orders"]]
        extractor.connection = mock_client

        tables = extractor.get_tables()

        assert tables == ["users", "orders"]
        mock_client.execute.assert_called_once_with("SHOW TABLES")

    def test_extract_table_ddl_mocked(self, extractor, config):
        """测试提取表 DDL (mock)"""
        mock_client = Mock()
        mock_ddl = "CREATE TABLE users (id UInt32, name String) ENGINE = MergeTree() ORDER BY id"
        mock_client.execute.return_value = [[mock_ddl]]
        extractor.connection = mock_client

        result = extractor.extract_table_ddl("users")

        assert result.table_name == "users"
        assert result.ddl == mock_ddl
        assert result.database == "testdb"
        mock_client.execute.assert_called_once_with("SHOW CREATE TABLE `users`")

    def test_extract_all_ddl_mocked(self, extractor):
        """测试提取所有表 DDL (mock)"""
        mock_client = Mock()
        mock_client.execute.side_effect = [
            [["users"], ["orders"]],  # SHOW TABLES
            [["CREATE TABLE users (id UInt32)"]],  # SHOW CREATE TABLE users
            [["CREATE TABLE orders (id UInt32)"]],  # SHOW CREATE TABLE orders
        ]
        extractor.config = {"host": "localhost", "port": 9000, "database": "testdb", "user": "default", "password": ""}

        with patch.object(extractor, 'connect') as mock_connect:
            with patch.object(extractor, 'disconnect') as mock_disconnect:
                extractor.connection = mock_client
                result = extractor.extract_all_ddl()

        assert len(result) == 2
        assert result[0]["table_name"] == "users"
        assert result[1]["table_name"] == "orders"


class TestPostgreSQLDDLExtractor:
    """PostgreSQL DDL 提取器测试"""

    @pytest.fixture
    def config(self):
        return {
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "user": "postgres",
            "password": "secret"
        }

    @pytest.fixture
    def extractor(self, config):
        return PostgreSQLDDLExtractor(config)

    def test_init(self, extractor, config):
        """测试初始化"""
        assert extractor.config == config
        assert extractor.connection is None

    def test_get_tables_mocked(self, extractor):
        """测试获取表列表 (mock)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [["users"], ["orders"]]
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        extractor.connection = mock_conn

        tables = extractor.get_tables()

        assert tables == ["users", "orders"]
        mock_cursor.execute.assert_called_once()

    def test_extract_table_ddl_mocked(self, extractor, config):
        """测试提取表 DDL (mock)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.side_effect = [
            # Columns
            [["id", "integer", None, None, None, "NO", None],
             ["name", "character varying", 255, None, None, "YES", None]],
            # Primary keys
            [["id"]],
            # Foreign keys
            []
        ]
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        extractor.connection = mock_conn

        result = extractor.extract_table_ddl("users")

        assert result.table_name == "users"
        assert result.database == "testdb"
        assert "CREATE TABLE users" in result.ddl
        assert "id integer NOT NULL" in result.ddl
        assert "PRIMARY KEY (id)" in result.ddl

    def test_generate_ddl_with_foreign_keys(self, extractor):
        """测试生成带外键的 DDL"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.side_effect = [
            # Columns
            [["id", "integer", None, None, None, "NO", None],
             ["user_id", "integer", None, None, None, "YES", None]],
            # Primary keys
            [["id"]],
            # Foreign keys
            [["user_id", "users", "id"]]
        ]
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        extractor.connection = mock_conn

        result = extractor.extract_table_ddl("orders")

        assert "FOREIGN KEY (user_id) REFERENCES users(id)" in result.ddl

    def test_generate_ddl_numeric_with_scale(self, extractor):
        """测试生成带精度的 numeric 类型 DDL"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.side_effect = [
            # Columns
            [["price", "numeric", None, 10, 2, "YES", None],
             ["quantity", "numeric", None, 5, None, "YES", None]],
            # Primary keys
            [],
            # Foreign keys
            []
        ]
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        extractor.connection = mock_conn

        result = extractor.extract_table_ddl("products")

        assert "numeric(10,2)" in result.ddl
        assert "numeric(5)" in result.ddl


class TestMySQLDDLExtractor:
    """MySQL DDL 提取器测试"""

    @pytest.fixture
    def config(self):
        return {
            "host": "localhost",
            "port": 3306,
            "database": "testdb",
            "user": "root",
            "password": "secret"
        }

    @pytest.fixture
    def extractor(self, config):
        return MySQLDDLExtractor(config)

    def test_init(self, extractor, config):
        """测试初始化"""
        assert extractor.config == config
        assert extractor.connection is None

    def test_get_tables_mocked(self, extractor):
        """测试获取表列表 (mock)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [["users"], ["orders"]]
        mock_conn.cursor.return_value = mock_cursor
        extractor.connection = mock_conn

        tables = extractor.get_tables()

        assert tables == ["users", "orders"]
        mock_cursor.execute.assert_called_once_with("SHOW TABLES")
        mock_cursor.close.assert_called_once()

    def test_extract_table_ddl_mocked(self, extractor, config):
        """测试提取表 DDL (mock)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_ddl = "CREATE TABLE `users` (`id` int NOT NULL, `name` varchar(255), PRIMARY KEY (`id`))"
        mock_cursor.fetchone.return_value = ("users", mock_ddl)
        mock_conn.cursor.return_value = mock_cursor
        extractor.connection = mock_conn

        result = extractor.extract_table_ddl("users")

        assert result.table_name == "users"
        assert result.ddl == mock_ddl
        assert result.database == "testdb"
        mock_cursor.execute.assert_called_once_with("SHOW CREATE TABLE `users`")
        mock_cursor.close.assert_called_once()

    def test_extract_table_ddl_empty_result(self, extractor):
        """测试提取表 DDL 返回空结果"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        extractor.connection = mock_conn

        with pytest.raises(ValueError, match="No DDL returned"):
            extractor.extract_table_ddl("nonexistent")


class TestDDLExtractorIntegration:
    """DDLExtractor 集成测试"""

    def test_clickhouse_full_flow(self):
        """测试 ClickHouse 完整流程"""
        config = {
            "host": "localhost",
            "port": 9000,
            "database": "default",
            "user": "default",
            "password": ""
        }

        with patch.object(ClickHouseDDLExtractor, 'connect') as mock_connect:
            with patch.object(ClickHouseDDLExtractor, 'disconnect') as mock_disconnect:
                with patch.object(ClickHouseDDLExtractor, 'get_tables', return_value=["users"]):
                    with patch.object(ClickHouseDDLExtractor, 'extract_table_ddl', return_value=TableDDL("users", "CREATE TABLE users", "default")):
                        extractor = DDLExtractor("clickhouse", config)
                        result = extractor.extract_all_ddl()

        assert len(result) == 1
        assert result[0]["table_name"] == "users"

    def test_get_tables_interface(self):
        """测试 get_tables 接口"""
        config = {"host": "localhost", "port": 3306, "database": "testdb", "user": "root", "password": ""}

        with patch.object(MySQLDDLExtractor, 'connect') as mock_connect:
            with patch.object(MySQLDDLExtractor, 'disconnect') as mock_disconnect:
                with patch.object(MySQLDDLExtractor, 'get_tables', return_value=["table1", "table2"]):
                    extractor = DDLExtractor("mysql", config)
                    tables = extractor.get_tables()

        assert tables == ["table1", "table2"]
        mock_connect.assert_called_once()
        mock_disconnect.assert_called_once()

    def test_extract_table_ddl_interface(self):
        """测试 extract_table_ddl 接口"""
        config = {"host": "localhost", "port": 5432, "database": "testdb", "user": "postgres", "password": ""}

        with patch.object(PostgreSQLDDLExtractor, 'connect') as mock_connect:
            with patch.object(PostgreSQLDDLExtractor, 'disconnect') as mock_disconnect:
                with patch.object(PostgreSQLDDLExtractor, 'extract_table_ddl', return_value=TableDDL("users", "CREATE TABLE users", "testdb")):
                    extractor = DDLExtractor("postgresql", config)
                    result = extractor.extract_table_ddl("users")

        assert result["table_name"] == "users"
        assert result["ddl"] == "CREATE TABLE users"
        assert result["database"] == "testdb"
        mock_connect.assert_called_once()
        mock_disconnect.assert_called_once()


class TestTableDDL:
    """TableDDL 数据类测试"""

    def test_dataclass_creation(self):
        """测试数据类创建"""
        ddl = TableDDL(table_name="users", ddl="CREATE TABLE users (id INT)")
        assert ddl.table_name == "users"
        assert ddl.ddl == "CREATE TABLE users (id INT)"
        assert ddl.database is None

    def test_dataclass_with_database(self):
        """测试带数据库的数据类创建"""
        ddl = TableDDL(table_name="users", ddl="CREATE TABLE users (id INT)", database="testdb")
        assert ddl.database == "testdb"


class TestBaseDDLExtractor:
    """BaseDDLExtractor 基类测试"""

    def test_abstract_methods(self):
        """测试抽象方法"""
        with pytest.raises(TypeError):
            BaseDDLExtractor({})

    def test_concrete_implementation(self):
        """测试具体实现"""
        class ConcreteExtractor(BaseDDLExtractor):
            def connect(self):
                self.connection = "connected"
            def disconnect(self):
                self.connection = None
            def get_tables(self):
                return ["table1"]
            def extract_table_ddl(self, table_name):
                return TableDDL(table_name, f"CREATE TABLE {table_name}", self.config.get("database"))

        extractor = ConcreteExtractor({"database": "testdb"})
        assert extractor.config == {"database": "testdb"}
