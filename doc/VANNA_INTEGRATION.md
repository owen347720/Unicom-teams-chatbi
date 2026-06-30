# Vanna 集成设计

## Vanna 简介

Vanna 是一个开源的 Python RAG（Retrieval-Augmented Generation）框架，专为 Text2SQL 任务设计。它通过训练数据管理（DDL、问题-SQL对、文档）来提高 SQL 生成的准确性。

## 核心组件

### 1. Vanna Library

**安装：**
```bash
pip install vanna
```

**初始化：**
```python
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn = MyVanna(config={
    'api_key': 'your-minimax-api-key',
    'model': 'MiniMax-M2.7',
    'api_base': 'http://10.242.52.62:9924/v1',
    'path': '/data/chromadb',
})
```

### 2. ChromaDB Vector Store

**存储内容：**
- DDL 信息（表结构定义）
- 训练数据（问题-SQL对）
- 文档信息（可选，业务文档）

**向量检索：**
- 使用相似度搜索（cosine similarity）
- 检索 top-k 相关示例
- 提供给 LLM 作为上下文

### 3. MiniMax-M2.7 LLM

**配置：**
- Endpoint: `http://10.242.52.62:9924`
- Model: `MiniMax-M2.7`
- OpenAI 兼容接口

**调用方式：**
```python
# Vanna 使用 OpenAI 兼容接口
response = vn.generate_sql(
    question="查询昨天销售额前10的产品",
    table_metadata="...",  # DDL
    training_data="...",   # 相似示例
)
```

## Vanna Service 设计

### 核心类设计

```python
# vanna-service/app/vanna_integration.py

from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
from typing import List, Dict
import logging

class VannaService(ChromaDB_VectorStore, OpenAI_Chat):
    """
    Vanna + ChromaDB + MiniMax-M2.7 集成服务
    """
    
    def __init__(self, config: dict):
        """
        初始化 Vanna Service
        
        Args:
            config: {
                'api_key': MiniMax API key,
                'model': 'MiniMax-M2.7',
                'api_base': 'http://10.242.52.62:9924/v1',
                'path': '/data/chromadb',
            }
        """
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)
        
        self.logger = logging.getLogger(__name__)
    
    def train_with_ddl(self, datasource_name: str, ddl: str):
        """
        训练 DDL 信息
        
        Args:
            datasource_name: 数据源名称（用于区分不同数据源）
            ddl: 表的 DDL 定义
        """
        try:
            # Vanna 的 train 方法
            self.train(ddl=ddl, datasource=datasource_name)
            self.logger.info(f"DDL trained: {datasource_name}")
        except Exception as e:
            self.logger.error(f"DDL training failed: {e}")
            raise
    
    def train_with_sql(self, datasource_name: str, question: str, sql: str):
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
                datasource=datasource_name
            )
            self.logger.info(f"SQL trained: {question}")
        except Exception as e:
            self.logger.error(f"SQL training failed: {e}")
            raise
    
    def generate_sql_for_question(
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
                'similar_questions': 相似问题列表,
            }
        """
        try:
            # Vanna 的 generate_sql 方法
            sql = self.generate_sql(
                question=question,
                datasource=datasource_name
            )
            
            # 获取相似问题（用于前端展示）
            similar = self.get_similar_question_sql(question)
            
            return {
                'sql': sql,
                'confidence': self.calculate_confidence(question, sql),
                'similar_questions': similar,
            }
        except Exception as e:
            self.logger.error(f"SQL generation failed: {e}")
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
        return self.get_similar_question_sql(question, n=n)
    
    def extract_ddl_from_database(
        self, 
        db_type: str, 
        connection_config: dict
    ) -> List[Dict]:
        """
        从数据库提取 DDL
        
        Args:
            db_type: clickhouse / postgresql / mysql
            connection_config: 连接配置
            
        Returns:
            [{table_name, ddl}]
        """
        from ddl_extractor import DDLExtractor
        
        extractor = DDLExtractor(db_type, connection_config)
        return extractor.extract_all_ddl()
```

### DDL Extractor

```python
# vanna-service/app/ddl_extractor.py

from typing import List, Dict
import logging

class DDLExtractor:
    """
    从不同数据库类型提取 DDL
    """
    
    def __init__(self, db_type: str, connection_config: dict):
        self.db_type = db_type
        self.config = connection_config
        self.logger = logging.getLogger(__name__)
    
    def extract_all_ddl(self) -> List[Dict]:
        """
        提取所有表的 DDL
        
        Returns:
            [{table_name, ddl}]
        """
        if self.db_type == 'clickhouse':
            return self._extract_clickhouse_ddl()
        elif self.db_type == 'postgresql':
            return self._extract_postgresql_ddl()
        elif self.db_type == 'mysql':
            return self._extract_mysql_ddl()
        else:
            raise ValueError(f"Unsupported db type: {self.db_type}")
    
    def _extract_clickhouse_ddl(self) -> List[Dict]:
        """提取 ClickHouse DDL"""
        from clickhouse_driver import Client
        
        client = Client(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['username'],
            password=self.config['password'],
            database=self.config['database']
        )
        
        # 获取所有表
        tables = client.execute(
            "SELECT name FROM system.tables "
            "WHERE database = '{database}'"
        )
        
        ddl_list = []
        for table_name in tables:
            # 获取表的 DDL
            result = client.execute(
                f"SHOW CREATE TABLE {table_name}"
            )
            ddl = result[0][0]
            ddl_list.append({
                'table_name': table_name,
                'ddl': ddl
            })
        
        return ddl_list
    
    def _extract_postgresql_ddl(self) -> List[Dict]:
        """提取 PostgreSQL DDL"""
        import psycopg2
        
        conn = psycopg2.connect(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['username'],
            password=self.config['password'],
            database=self.config['database']
        )
        
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public'"
        )
        tables = cursor.fetchall()
        
        ddl_list = []
        for table_name in tables:
            # 使用 pg_get_tabledef 函数
            cursor.execute(
                f"SELECT pg_get_tabledef('{table_name}'::regclass)"
            )
            ddl = cursor.fetchone()[0]
            ddl_list.append({
                'table_name': table_name,
                'ddl': ddl
            })
        
        conn.close()
        return ddl_list
    
    def _extract_mysql_ddl(self) -> List[Dict]:
        """提取 MySQL DDL"""
        import mysql.connector
        
        conn = mysql.connector.connect(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['username'],
            password=self.config['password'],
            database=self.config['database']
        )
        
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        ddl_list = []
        for table_name in tables:
            cursor.execute(f"SHOW CREATE TABLE {table_name[0]}")
            result = cursor.fetchone()
            ddl = result[1]
            ddl_list.append({
                'table_name': table_name[0],
                'ddl': ddl
            })
        
        conn.close()
        return ddl_list
```

## API 端点设计

### Vanna Service REST API

```python
# vanna-service/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from vanna_integration import VannaService

app = FastAPI()
vn_service = VannaService(config={
    'api_key': os.getenv('MINIMAX_API_KEY'),
    'model': 'MiniMax-M2.7',
    'api_base': 'http://10.242.52.62:9924/v1',
    'path': '/data/chromadb',
})

class TrainDDLRequest(BaseModel):
    datasource_name: str
    ddl: str

class TrainSQLRequest(BaseModel):
    datasource_name: str
    question: str
    sql: str

class GenerateSQLRequest(BaseModel):
    datasource_name: str
    question: str

@app.post("/train/ddl")
async def train_ddl(request: TrainDDLRequest):
    """训练 DDL 信息"""
    try:
        vn_service.train_with_ddl(
            request.datasource_name,
            request.ddl
        )
        return {"success": True, "message": "DDL trained"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train/sql")
async def train_sql(request: TrainSQLRequest):
    """训练问题-SQL对"""
    try:
        vn_service.train_with_sql(
            request.datasource_name,
            request.question,
            request.sql
        )
        return {"success": True, "message": "SQL trained"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_sql(request: GenerateSQLRequest):
    """生成 SQL"""
    try:
        result = vn_service.generate_sql_for_question(
            request.datasource_name,
            request.question
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/similar/{question}")
async def get_similar(question: str, n: int = 5):
    """获取相似训练数据"""
    try:
        similar = vn_service.get_similar_training_data(question, n)
        return {"similar_questions": similar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}
```

## ChromaDB 管理

### 数据存储结构

ChromaDB 使用 Collections 组织数据：

```python
# ChromaDB 自动创建以下 collections:
# 1. ddl_collection - 存储 DDL 信息
# 2. sql_collection - 存储问题-SQL对
# 3. documentation_collection - 存储文档（可选）
```

### 持久化配置

```python
# ChromaDB 持久化路径
chromadb_path = '/data/chromadb'

# Docker volume 映射
volumes:
  - chromadb-data:/data/chromadb
```

### 备份和恢复

**备份脚本：**
```python
# scripts/backup_chromadb.py

import chromadb
import json
from datetime import datetime

def backup_chromadb():
    client = chromadb.PersistentClient(path='/data/chromadb')
    
    # 获取所有 collections
    collections = client.list_collections()
    
    backup_data = {}
    for collection in collections:
        # 获取所有数据
        results = collection.get()
        backup_data[collection.name] = {
            'ids': results['ids'],
            'documents': results['documents'],
            'metadatas': results['metadatas'],
            'embeddings': results['embeddings'],
        }
    
    # 保存备份
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'/data/backups/chromadb_backup_{timestamp}.json'
    
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f)
    
    print(f"Backup saved to {backup_file}")

if __name__ == '__main__':
    backup_chromadb()
```

**恢复脚本：**
```python
# scripts/restore_chromadb.py

import chromadb
import json

def restore_chromadb(backup_file: str):
    client = chromadb.PersistentClient(path='/data/chromadb')
    
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    
    for collection_name, data in backup_data.items():
        # 创建或获取 collection
        collection = client.get_or_create_collection(collection_name)
        
        # 清空现有数据
        existing_ids = collection.get()['ids']
        if existing_ids:
            collection.delete(ids=existing_ids)
        
        # 恢复数据
        collection.add(
            ids=data['ids'],
            documents=data['documents'],
            metadatas=data['metadatas'],
            embeddings=data['embeddings'],
        )
    
    print(f"Restored from {backup_file}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python restore_chromadb.py <backup_file>")
        sys.exit(1)
    
    restore_chromadb(sys.argv[1])
```

## MiniMax API 集成

### OpenAI 兼容接口

MiniMax 提供 OpenAI 兼容的 API，Vanna 可以直接使用：

```python
# Vanna 配置
config = {
    'api_key': os.getenv('MINIMAX_API_KEY'),
    'model': 'MiniMax-M2.7',
    'api_base': 'http://10.242.52.62:9924/v1',  # MiniMax endpoint
}

# Vanna 内部调用方式（类似 OpenAI）
import openai

openai.api_key = config['api_key']
openai.api_base = config['api_base']

response = openai.ChatCompletion.create(
    model=config['model'],
    messages=[
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
    ]
)
```

### 错误处理

```python
# 常见错误：
# 1. API Key 错误 - 401 Unauthorized
# 2. Endpoint 不可达 - Connection Error
# 3. Model 不存在 - 404 Not Found
# 4. Token 限制 - 400 Bad Request

# 重试机制
max_retries = 3
retry_delay = 2  # seconds

for attempt in range(max_retries):
    try:
        result = vn.generate_sql(question)
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        time.sleep(retry_delay)
```

## 性能优化

### 1. 向量检索优化

- ChromaDB 默认使用 cosine similarity
- 可以调整 top-k 参数（默认 5）
- 对于大型训练数据集，考虑使用索引

### 2. 缓存机制

- 缓存相似问题的 SQL 结果
- 减少 MiniMax API 调用次数
- 使用 Redis 或内存缓存

### 3. 训练数据质量

- 定期清理低质量训练数据
- 添加多样化的示例
- 针对不同数据源添加专属训练数据

## 监控和日志

### 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/vanna.log'),
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)
```

### 关键指标

- SQL 生成成功率
- SQL 生成时间
- ChromaDB 查询时间
- MiniMax API 响应时间
- 训练数据数量

## 完整设计文档

完整设计文档见：`docs/superpowers/specs/2026-06-30-vanna-text2sql-design.md`

## 更新日期

2026-06-30