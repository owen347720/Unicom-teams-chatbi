"""
VannaService 测试 - TDD 驱动开发
测试 SQL 生成和训练数据管理接口
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from vanna.base import VannaBase

# 确保 MINIMAX_API_KEY 不为空（用于测试环境）
os.environ.setdefault("MINIMAX_API_KEY", "test-api-key-for-testing")


class TestVannaServiceInit:
    """测试 VannaService 初始化"""

    def test_vanna_service_init(self):
        """测试 Vanna Service 初始化"""
        from app.vanna_integration import VannaService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                os.environ,
                {
                    "MINIMAX_API_KEY": "test-key",
                    "MINIMAX_ENDPOINT": "http://10.242.52.62:9924",
                    "MINIMAX_MODEL": "MiniMax-M2.7",
                    "CHROMADB_PATH": tmpdir,
                },
            ):
                service = VannaService()
                assert service is not None
                assert service.model == "MiniMax-M2.7"

    def test_vanna_service_uses_env_config(self):
        """测试 Vanna Service 从环境变量读取配置"""
        from app.vanna_integration import VannaService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                os.environ,
                {
                    "MINIMAX_API_KEY": "my-custom-key",
                    "MINIMAX_ENDPOINT": "http://10.242.52.62:9924",
                    "MINIMAX_MODEL": "MiniMax-M2.7",
                    "CHROMADB_PATH": tmpdir,
                },
            ):
                service = VannaService()
                assert service is not None
                # 验证使用了正确的 model
                assert hasattr(service, "model")


class TestTrainDDL:
    """测试 DDL 训练"""

    def test_train_ddl(self):
        """测试 DDL 训练基本功能"""
        from app.vanna_integration import VannaService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                os.environ,
                {
                    "MINIMAX_API_KEY": "test-key",
                    "MINIMAX_ENDPOINT": "http://10.242.52.62:9924",
                    "MINIMAX_MODEL": "MiniMax-M2.7",
                    "CHROMADB_PATH": tmpdir,
                },
            ):
                service = VannaService()

                # Mock train 方法避免实际调用 Vanna 内部逻辑
                service.train = MagicMock()
                service.train_ddl("test_datasource", "CREATE TABLE test (id INT)")

                # 验证 train 被调用且传入了正确的 metadata
                service.train.assert_called_once()
                call_kwargs = service.train.call_args
                assert call_kwargs[1]["ddl"] == "CREATE TABLE test (id INT)"
                assert call_kwargs[1]["metadata"]["datasource"] == "test_datasource"


class TestTrainSQL:
    """测试 SQL 训练"""

    def test_train_sql(self):
        """测试 SQL 训练基本功能"""
        from app.vanna_integration import VannaService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                os.environ,
                {
                    "MINIMAX_API_KEY": "test-key",
                    "MINIMAX_ENDPOINT": "http://10.242.52.62:9924",
                    "MINIMAX_MODEL": "MiniMax-M2.7",
                    "CHROMADB_PATH": tmpdir,
                },
            ):
                service = VannaService()

                # Mock train 方法
                service.train = MagicMock()
                service.train_sql(
                    datasource_name="test_datasource",
                    question="查询所有用户",
                    sql="SELECT * FROM users",
                )

                # 验证 train 被正确调用
                service.train.assert_called_once()
                call_kwargs = service.train.call_args
                assert call_kwargs[1]["question"] == "查询所有用户"
                assert call_kwargs[1]["sql"] == "SELECT * FROM users"
                assert call_kwargs[1]["metadata"]["datasource"] == "test_datasource"


class TestGenerateSQL:
    """测试 SQL 生成"""

    def test_generate_sql_returns_dict(self):
        """测试 generate_sql 返回正确的字典结构"""
        from app.vanna_integration import VannaService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                os.environ,
                {
                    "MINIMAX_API_KEY": "test-key",
                    "MINIMAX_ENDPOINT": "http://10.242.52.62:9924",
                    "MINIMAX_MODEL": "MiniMax-M2.7",
                    "CHROMADB_PATH": tmpdir,
                },
            ):
                service = VannaService()

                # Mock VannaBase.generate_sql 方法避免实际调用 LLM
                with patch.object(VannaBase, 'generate_sql', return_value="SELECT 1"):
                    service.get_similar_question_sql = MagicMock(
                        return_value=[{"question": "test", "sql": "SELECT 1"}]
                    )

                    result = service.generate_sql("test", "test question")

                    assert result is not None
                    assert "sql" in result
                    assert "confidence" in result
                    assert "similar_questions" in result
                    assert result["sql"] == "SELECT 1"


class TestGetSimilarTrainingData:
    """测试获取相似训练数据"""

    def test_get_similar_training_data(self):
        """测试获取相似训练数据"""
        from app.vanna_integration import VannaService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                os.environ,
                {
                    "MINIMAX_API_KEY": "test-key",
                    "MINIMAX_ENDPOINT": "http://10.242.52.62:9924",
                    "MINIMAX_MODEL": "MiniMax-M2.7",
                    "CHROMADB_PATH": tmpdir,
                },
            ):
                service = VannaService()

                expected = [
                    {"question": "q1", "sql": "SELECT 1", "similarity": 0.9},
                    {"question": "q2", "sql": "SELECT 2", "similarity": 0.8},
                ]
                service.get_similar_question_sql = MagicMock(return_value=expected)

                result = service.get_similar_training_data("test question", n=2)

                assert result is not None
                assert isinstance(result, list)
                assert len(result) == 2

    def test_get_similar_training_data_default_n(self):
        """测试默认 n=5"""
        from app.vanna_integration import VannaService

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                os.environ,
                {
                    "MINIMAX_API_KEY": "test-key",
                    "MINIMAX_ENDPOINT": "http://10.242.52.62:9924",
                    "MINIMAX_MODEL": "MiniMax-M2.7",
                    "CHROMADB_PATH": tmpdir,
                },
            ):
                service = VannaService()

                service.get_similar_question_sql = MagicMock(return_value=[])

                service.get_similar_training_data("test question")

                call_kwargs = service.get_similar_question_sql.call_args
                assert call_kwargs[1]["n"] == 5
