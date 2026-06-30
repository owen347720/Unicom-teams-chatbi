# Task 4: 实现 Vanna 集成核心

## 任务描述

实现 VannaService 核心类，提供 SQL 生成和训练数据管理接口。这是 Vanna Service 的核心功能。

## 文件清单

需要创建的文件：
- `vanna-service/app/vanna_integration.py`
- `vanna-service/tests/__init__.py`（空文件）
- `vanna-service/tests/test_vanna_integration.py`

## 接口定义

此任务产生：`VannaService` 类提供以下接口：
- `train_ddl(datasource_name: str, ddl: str)` - 训练 DDL 信息
- `train_sql(datasource_name: str, question: str, sql: str)` - 训练问题-SQL对
- `generate_sql(datasource_name: str, question: str) -> Dict` - 生成 SQL
- `get_similar_training_data(question: str, n: int = 5) -> List[Dict]` - 获取相似训练数据

此任务消费：
- MiniMax API (endpoint: 10.242.52.62:9924)
- ChromaDB
- app/config.py 中的配置

## Global Constraints

必须遵循以下全局约束：
- MiniMax endpoint: `10.242.52.62:9924`
- MiniMax model: `MiniMax-M2.7`
- ChromaDB 持久化路径: `/data/chromadb`
- 使用 Vanna 库集成 ChromaDB_VectorStore 和 OpenAI_Chat
- 使用 loguru 进行日志记录
- 使用 metadata 字段标记数据源（{'datasource': datasource_name}）

## TDD 流程

### Step 1: 编写测试（失败）

```python
# vana-service/tests/test_vanna_integration.py

import pytest
from app.vanna_integration import VannaService

def test_vanna_service_init():
    """测试 Vanna Service 初始化"""
    service = VannaService()
    assert service is not None
    assert service.model == "MiniMax-M2.7"

def test_train_ddl():
    """测试 DDL 训练"""
    service = VannaService()
    service.train_ddl("test_datasource", "CREATE TABLE test (id INT)")
    # 应该能成功存储到 ChromaDB
    assert True

def test_train_sql():
    """测试 SQL 训练"""
    service = VannaService()
    service.train_sql(
        datasource_name="test_datasource",
        question="查询所有用户",
        sql="SELECT * FROM users"
    )
    assert True

def test_generate_sql():
    """测试 SQL 生成"""
    service = VannaService()
    # 需要先训练数据
    service.train_sql("test", "test question", "SELECT 1")
    
    result = service.generate_sql("test", "test question")
    assert result is not None
    assert 'sql' in result
```

### Step 2: 运行测试（失败）

```bash
cd vanna-service
pytest tests/test_vanna_integration.py -v
```

Expected: FAIL - ModuleNotFoundError

### Step 3: 实现 VannaService

```python
# vana-service/app/vanna_integration.py

from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
from typing import Dict, List, Optional
from loguru import logger
import os

class VannaService(ChromaDB_VectorStore, OpenAI_Chat):
    """
    Vanna + ChromaDB + MiniMax-M2.7 集成服务
    提供 SQL 生成和训练数据管理
    """
    
    def __init__(self):
        """
        初始化 Vanna Service
        配置 MiniMax endpoint 和 ChromaDB
        """
        config = {
            'api_key': os.getenv('MINIMAX_API_KEY', ''),
            'model': os.getenv('MINIMAX_MODEL', 'MiniMax-M2.7'),
            'api_base': os.getenv('MINIMAX_ENDPOINT', 'http://10.242.52.62:9924') + '/v1',
            'path': os.getenv('CHROMADB_PATH', '/data/chromadb'),
        }
        
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
        
        self.model = config['model']
        logger.info(f"VannaService initialized with model: {self.model}")
    
    def train_ddl(self, datasource_name: str, ddl: str):
        """
        训练 DDL 信息
        
        Args:
            datasource_name: 数据源名称
            ddl: 表的 DDL 定义
        """
        try:
            # 使用 metadata 标记数据源
            self.train(ddl=ddl, metadata={'datasource': datasource_name})
            logger.info(f"DDL trained for {datasource_name}: {ddl[:50]}...")
        except Exception as e:
            logger.error(f"DDL training failed: {e}")
            raise
    
    def train_sql(
        self,
        datasource_name: str,
        question: str,
        sql: str
    ):
        """
        训练问题-SQL对
        
        Args:
            datasource_name: 数据源名称
            question: 自然语言问题
            sql: SQL 查询语句
        """
        try:
            self.train(
                question=question,
                sql=sql,
                metadata={'datasource': datasource_name}
            )
            logger.info(f"SQL trained: {question}")
        except Exception as e:
            logger.error(f"SQL training failed: {e}")
            raise
    
    def generate_sql(
        self,
        datasource_name: str,
        question: str
    ) -> Dict:
        """
        根据问题生成 SQL
        
        Args:
            datasource_name: 数据源名称
            question: 自然语言问题
            
        Returns:
            {
                'sql': 生成的SQL,
                'confidence': 置信度,
                'similar_questions': 相似问题列表
            }
        """
        try:
            # 使用 Vanna 的 generate_sql 方法
            # 注意: 需要过滤特定数据源的 training data
            sql = self.generate_sql(
                question=question,
                metadata={'datasource': datasource_name}
            )
            
            # 获取相似问题
            similar = self.get_similar_question_sql(question, n=5)
            
            logger.info(f"SQL generated for {datasource_name}: {sql[:100]}...")
            
            return {
                'sql': sql,
                'confidence': 0.8,  # Vanna 不提供置信度,默认返回
                'similar_questions': similar
            }
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise
    
    def get_similar_training_data(
        self,
        question: str,
        n: int = 5
    ) -> List[Dict]:
        """
        获取相似训练数据
        
        Args:
            question: 问题
            n: 返回数量
            
        Returns:
            [{question, sql, similarity}]
        """
        try:
            similar = self.get_similar_question_sql(question, n=n)
            return similar
        except Exception as e:
            logger.error(f"Similar data retrieval failed: {e}")
            return []
```

### Step 4: 运行测试（通过）

```bash
cd vanna-service
pytest tests/test_vanna_integration.py -v
```

Expected: PASS（部分测试可能需要 MiniMax API Key，可以跳过或 mock）

### Step 5: Commit

```bash
git add vanna-service/app/vanna_integration.py vanna-service/tests/
git commit -m "feat: implement VannaService core

- Implement VannaService class with ChromaDB and OpenAI Chat
- Add train_ddl and train_sql methods
- Add generate_sql method
- Add get_similar_training_data method
- Add unit tests with TDD approach"
```

## 注意事项

1. **测试环境**: 测试可能需要 MiniMax API Key，可以使用环境变量或 mock
2. **Vanna 集成**: 继承 ChromaDB_VectorStore 和 OpenAI_Chat，需要正确初始化
3. **metadata 使用**: 使用 metadata 字段标记数据源，便于后续过滤
4. **日志记录**: 使用 loguru 记录关键操作和错误

## 上下文说明

这是 Vanna Service 的核心实现任务，后续任务会使用这个类：
- Task 5: FastAPI 服务端点会调用 VannaService
- Task 6: DDL 提取器会将提取的 DDL 通过 VannaService.train_ddl 存储到 ChromaDB

## 报告要求

完成后，请在 `/Users/owen/coding/2026-自学/Text2Sql/.superpowers/sdd/task-4-report.md` 编写报告，包含：
1. TDD 流程执行情况（测试失败→实现→测试通过）
2. 测试运行结果
3. Commit hash
4. 任何问题或关注点（特别是 MiniMax API Key 相关）
5. 返回状态（DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED）