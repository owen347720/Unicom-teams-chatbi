"""
FastAPI 端点测试 - TDD 驱动开发
测试所有 REST API 端点
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# 确保 MINIMAX_API_KEY 不为空（用于测试环境）
os.environ.setdefault("MINIMAX_API_KEY", "test-api-key-for-testing")


@pytest.fixture
def mock_vanna_service():
    """模拟 VannaService"""
    mock = MagicMock()
    mock.train_ddl = MagicMock()
    mock.train_sql = MagicMock()
    mock.generate_sql = MagicMock(return_value={
        "sql": "SELECT * FROM users WHERE name = 'test'",
        "confidence": 0.85,
        "similar_questions": [
            {"question": "查询用户", "sql": "SELECT * FROM users", "similarity": 0.9}
        ]
    })
    mock.get_similar_training_data = MagicMock(return_value=[
        {"question": "查询用户", "sql": "SELECT * FROM users", "similarity": 0.9},
        {"question": "获取用户信息", "sql": "SELECT * FROM users LIMIT 10", "similarity": 0.8}
    ])
    return mock


@pytest.fixture
def client(mock_vanna_service):
    """创建测试客户端"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(
            os.environ,
            {
                "MINIMAX_API_KEY": "test-key",
                "MINIMAX_ENDPOINT": "http://10.242.52.62:9924",
                "MINIMAX_MODEL": "MiniMax-M2.7",
                "CHROMADB_PATH": tmpdir,
                "LOG_DIR": tmpdir,
            },
        ):
            from app.main import app, vanna_service
            # 替换 vanna_service
            with patch('app.main.vanna_service', mock_vanna_service):
                yield TestClient(app)


class TestHealthCheck:
    """测试健康检查端点"""

    def test_health_check(self, client):
        """测试健康检查返回正确状态"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "Vanna Service"


class TestTrainDDL:
    """测试 DDL 训练端点"""

    def test_train_ddl_endpoint(self, client, mock_vanna_service):
        """测试 DDL 训练端点"""
        payload = {
            "datasource_name": "test_datasource",
            "ddl": "CREATE TABLE users (id INT, name VARCHAR(100))"
        }
        response = client.post("/train/ddl", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "DDL trained successfully"
        # 验证 service 方法被调用
        mock_vanna_service.train_ddl.assert_called_once_with(
            datasource_name="test_datasource",
            ddl="CREATE TABLE users (id INT, name VARCHAR(100))"
        )

    def test_train_ddl_missing_fields(self, client):
        """测试 DDL 训练端点缺少字段"""
        payload = {"datasource_name": "test"}
        response = client.post("/train/ddl", json=payload)
        assert response.status_code == 422


class TestTrainSQL:
    """测试 SQL 训练端点"""

    def test_train_sql_endpoint(self, client, mock_vanna_service):
        """测试 SQL 训练端点"""
        payload = {
            "datasource_name": "test_datasource",
            "question": "查询所有用户",
            "sql": "SELECT * FROM users"
        }
        response = client.post("/train/sql", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "SQL trained successfully"
        # 验证 service 方法被调用
        mock_vanna_service.train_sql.assert_called_once_with(
            datasource_name="test_datasource",
            question="查询所有用户",
            sql="SELECT * FROM users"
        )

    def test_train_sql_missing_fields(self, client):
        """测试 SQL 训练端点缺少字段"""
        payload = {
            "datasource_name": "test",
            "question": "查询用户"
            # 缺少 sql
        }
        response = client.post("/train/sql", json=payload)
        assert response.status_code == 422


class TestGenerateSQL:
    """测试 SQL 生成端点"""

    def test_generate_endpoint(self, client, mock_vanna_service):
        """测试 SQL 生成端点"""
        payload = {
            "datasource_name": "test_datasource",
            "question": "查询所有用户"
        }
        response = client.post("/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["sql"] == "SELECT * FROM users WHERE name = 'test'"
        assert data["data"]["confidence"] == 0.85
        # 验证 service 方法被调用
        mock_vanna_service.generate_sql.assert_called_once_with(
            datasource_name="test_datasource",
            question="查询所有用户",
            schema_context=None,
        )

    def test_generate_missing_fields(self, client):
        """测试 SQL 生成端点缺少字段"""
        payload = {"datasource_name": "test"}
        response = client.post("/generate", json=payload)
        assert response.status_code == 422


class TestGetSimilar:
    """测试获取相似训练数据端点"""

    def test_get_similar_endpoint(self, client, mock_vanna_service):
        """测试获取相似训练数据端点"""
        response = client.get("/similar/查询用户")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) == 2
        assert data["data"][0]["question"] == "查询用户"
        # 验证 service 方法被调用
        mock_vanna_service.get_similar_training_data.assert_called_once_with(
            question="查询用户",
            n=5
        )

    def test_get_similar_with_limit(self, client, mock_vanna_service):
        """测试获取相似训练数据带限制"""
        response = client.get("/similar/查询用户?n=3")
        assert response.status_code == 200
        mock_vanna_service.get_similar_training_data.assert_called_once_with(
            question="查询用户",
            n=3
        )
