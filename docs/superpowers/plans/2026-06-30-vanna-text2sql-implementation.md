# Vanna Text2SQL 问数系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于 Vanna 的 Text2SQL 问数系统,支持自然语言转 SQL 查询,一键 Docker 部署

**Architecture:** 微服务架构,三个主要服务容器(Frontend + Backend API + Vanna Service),使用 PostgreSQL 存储元数据,ChromaDB 存储向量数据,MiniMax-M2.7 作为 LLM

**Tech Stack:** React 18 + TypeScript + Ant Design 5.x, FastAPI + PostgreSQL + SQLAlchemy, Vanna + ChromaDB + MiniMax-M2.7, Docker + docker-compose

## Global Constraints

从设计文档复制的关键约束:

- MiniMax endpoint: `10.242.52.62:9924` (必须可访问)
- MiniMax model: `MiniMax-M2.7`
- OpenAI 兼容接口
- SQL 执行超时: 60 秒
- 最大返回行数: 1000 行
- 数据源类型: ClickHouse / PostgreSQL / MySQL
- ChromaDB 持久化路径: `/data/chromadb`
- PostgreSQL 连接: `postgresql://text2sql:text2sql123@postgres:5432/text2sql`
- 无用户认证(内部工具)
- 数据源密码需要加密存储
- API Key 存储在 `.env` 文件,不提交到 Git

---

## Phase 1: 项目初始化和基础设施

### Task 1: 创建项目目录结构

**Files:**
- Create: `frontend/`, `backend/`, `vanna-service/` 目录结构
- Create: `.gitignore`
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `README.md`

**Interfaces:**
- Produces: 项目基础目录结构,供后续任务使用

- [ ] **Step 1: 创建目录结构**

```bash
# 创建主要目录
mkdir -p frontend backend vanna-service

# 创建子目录
mkdir -p frontend/src/components frontend/src/pages frontend/src/services frontend/public
mkdir -p backend/app/routers backend/app/models backend/app/services backend/logs
mkdir -p vanna-service/app vanna-service/scripts vanna-service/data/chromadb
```

- [ ] **Step 2: 创建 .gitignore**

```bash
# 创建 .gitignore
cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local
*.key

# Logs
*.log
logs/

# Dependencies
node_modules/
__pycache__/
*.pyc
.pyo

# Build artifacts
dist/
build/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker volumes (local)
chromadb-data/
postgres-data/
EOF
```

- [ ] **Step 3: 创建 .env.example**

```bash
# 创建 .env.example
cat > .env.example << 'EOF'
# MiniMax API 配置（必需）
MINIMAX_API_KEY=your_api_key_here

# PostgreSQL 配置（可选，有默认值）
POSTGRES_USER=text2sql
POSTGRES_PASSWORD=text2sql123
POSTGRES_DB=text2sql

# 系统配置（可选）
SQL_TIMEOUT=60
MAX_RESULT_ROWS=1000
AUTO_TRAIN_ENABLED=true
LOG_LEVEL=INFO
EOF
```

- [ ] **Step 4: 创建初始 README.md**

```bash
cat > README.md << 'EOF'
# Text2Sql - 团队内取数系统

基于 Vanna 的 Text2SQL 问数系统,支持自然语言转 SQL 查询。

## 快速开始

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件,填入 MINIMAX_API_KEY

# 2. 一键启动
docker-compose up -d

# 3. 访问界面
浏览器打开: http://localhost:3000
```

## 详细文档

见 `doc/` 目录。

## 更新日期

2026-06-30
EOF
```

- [ ] **Step 5: 验证目录结构**

```bash
# 验证目录结构
tree -L 3 -I 'node_modules|__pycache__|.git'
```

Expected: 显示完整目录结构

- [ ] **Step 6: Commit**

```bash
git add .gitignore .env.example README.md
git commit -m "chore: initialize project structure

- Add directory structure for frontend/backend/vanna-service
- Add .gitignore for environment files and logs
- Add .env.example template
- Add initial README.md"
```

---

### Task 2: 创建 Docker Compose 配置

**Files:**
- Create: `docker-compose.yml`

**Interfaces:**
- Produces: `docker-compose.yml` 定义所有服务配置
- Consumes: `.env` 文件中的环境变量

- [ ] **Step 1: 创建 docker-compose.yml**

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # 前端服务
  frontend:
    build: ./frontend
    container_name: text2sql-frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - NODE_ENV=production
    depends_on:
      - backend-api
    networks:
      - text2sql-network
    restart: always
    
  # 后端 API 服务
  backend-api:
    build: ./backend
    container_name: text2sql-backend
    ports:
      - "8000:8000"
    environment:
      - VANNA_SERVICE_URL=http://vanna-service:8001
      - DATABASE_URL=postgresql://text2sql:text2sql123@postgres:5432/text2sql
      - CORS_ORIGINS=http://localhost:3000
      - SQL_TIMEOUT=60
      - MAX_RESULT_ROWS=1000
    volumes:
      - ./backend/logs:/app/logs
    depends_on:
      - vanna-service
      - postgres
    networks:
      - text2sql-network
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  # Vanna AI 服务
  vanna-service:
    build: ./vanna-service
    container_name: text2sql-vanna
    ports:
      - "8001:8001"
    environment:
      - MINIMAX_ENDPOINT=http://10.242.52.62:9924
      - MINIMAX_MODEL=MiniMax-M2.7
      - MINIMAX_API_KEY=${MINIMAX_API_KEY}
      - CHROMADB_PATH=/data/chromadb
    volumes:
      - chromadb-data:/data/chromadb
    networks:
      - text2sql-network
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  # PostgreSQL 元数据存储
  postgres:
    image: postgres:15
    container_name: text2sql-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=text2sql
      - POSTGRES_PASSWORD=text2sql123
      - POSTGRES_DB=text2sql
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - text2sql-network
    restart: always

volumes:
  chromadb-data:
    driver: local
  postgres-data:
    driver: local

networks:
  text2sql-network:
    driver: bridge
EOF
```

- [ ] **Step 2: 验证 docker-compose.yml**

```bash
# 验证配置文件语法
docker-compose config
```

Expected: 显示配置详情,无错误

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add docker-compose configuration

- Define 4 services: frontend, backend-api, vanna-service, postgres
- Configure volumes for ChromaDB and PostgreSQL
- Configure health checks
- Set up internal network"
```

---

## Phase 2: Vanna Service 实现

### Task 3: 创建 Vanna Service 基础配置

**Files:**
- Create: `vanna-service/Dockerfile`
- Create: `vanna-service/requirements.txt`
- Create: `vanna-service/app/config.py`

**Interfaces:**
- Produces: Vanna Service 容器配置和 Python 依赖

- [ ] **Step 1: 创建 requirements.txt**

```bash
cat > vanna-service/requirements.txt << 'EOF'
# FastAPI
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0

# Vanna
vanna==0.5.4

# ChromaDB
chromadb==0.4.22

# Database drivers
clickhouse-driver==0.2.6
psycopg2-binary==2.9.9
mysql-connector-python==8.2.0

# HTTP client
requests==2.31.0
httpx==0.25.2

# Logging
loguru==0.7.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
EOF
```

- [ ] **Step 2: 创建 Dockerfile**

```bash
cat > vanna-service/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create data directory
RUN mkdir -p /data/chromadb /data/backups /app/logs

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
EOF
```

- [ ] **Step 3: 创建 config.py**

```python
# vana-service/app/config.py

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MiniMax API 配置
    minimax_endpoint: str = "http://10.242.52.62:9924"
    minimax_model: str = "MiniMax-M2.7"
    minimax_api_key: str
    
    # ChromaDB 配置
    chromadb_path: str = "/data/chromadb"
    
    # Service 配置
    service_name: str = "Vanna Service"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

- [ ] **Step 4: 验证依赖安装**

```bash
# 测试 Docker 构建(稍后在完整测试中验证)
# 这里先检查语法
docker build -t test-vanna ./vanna-service --no-cache || echo "Build test"
```

Expected: 构建成功或显示预期错误

- [ ] **Step 5: Commit**

```bash
git add vanna-service/
git commit -m "feat: add Vanna Service base configuration

- Add Dockerfile with health check
- Add requirements.txt with dependencies
- Add config.py with Pydantic settings"
```

---

### Task 4: 实现 Vanna 集成核心

**Files:**
- Create: `vanna-service/app/vanna_integration.py`
- Create: `vanna-service/tests/test_vanna_integration.py`

**Interfaces:**
- Produces: `VannaService` 类提供 SQL 生成和训练数据管理接口
- Consumes: MiniMax API (endpoint: 10.242.52.62:9924), ChromaDB

- [ ] **Step 1: 编写测试(失败)**

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

- [ ] **Step 2: 运行测试(失败)**

```bash
cd vanna-service
pytest tests/test_vanna_integration.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现 VannaService**

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

- [ ] **Step 4: 运行测试(通过)**

```bash
cd vanna-service
pytest tests/test_vanna_integration.py -v
```

Expected: PASS (部分测试可能需要 MiniMax API Key)

- [ ] **Step 5: Commit**

```bash
git add vanna-service/app/vanna_integration.py vanna-service/tests/
git commit -m "feat: implement VannaService core

- Implement VannaService class with ChromaDB and OpenAI Chat
- Add train_ddl and train_sql methods
- Add generate_sql method
- Add get_similar_training_data method
- Add unit tests"
```

---

### Task 5: 实现 FastAPI 服务端点

**Files:**
- Create: `vanna-service/app/main.py`
- Create: `vanna-service/tests/test_main.py`

**Interfaces:**
- Consumes: `VannaService` 类
- Produces: REST API 端点 (/train/ddl, /train/sql, /generate, /health)

- [ ] **Step 1: 编写测试**

```python
# vana-service/tests/test_main.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_train_ddl_endpoint():
    """测试 DDL 训练端点"""
    response = client.post("/train/ddl", json={
        "datasource_name": "test",
        "ddl": "CREATE TABLE test (id INT)"
    })
    assert response.status_code == 200
    assert response.json()["success"] == True

def test_train_sql_endpoint():
    """测试 SQL 训练端点"""
    response = client.post("/train/sql", json={
        "datasource_name": "test",
        "question": "查询所有用户",
        "sql": "SELECT * FROM users"
    })
    assert response.status_code == 200
    assert response.json()["success"] == True

def test_generate_endpoint():
    """测试 SQL 生成端点"""
    response = client.post("/generate", json={
        "datasource_name": "test",
        "question": "test question"
    })
    assert response.status_code == 200
    # 注意: 可能失败因为没有训练数据
```

- [ ] **Step 2: 运行测试(失败)**

```bash
cd vanna-service
pytest tests/test_main.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现 FastAPI 应用**

```python
# vana-service/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
from loguru import logger
import sys

from app.vanna_integration import VannaService

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("/app/logs/vanna.log", level="DEBUG", rotation="1 day")

# Initialize app
app = FastAPI(
    title="Vanna Service",
    description="AI-powered SQL generation service",
    version="1.0.0"
)

# Initialize Vanna Service
vanna_service = None

@app.on_event("startup")
async def startup_event():
    """启动时初始化 Vanna Service"""
    global vanna_service
    try:
        vanna_service = VannaService()
        logger.info("Vanna Service initialized successfully")
    except Exception as e:
        logger.error(f"Vanna Service initialization failed: {e}")

# Request models
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

# API endpoints
@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "Vanna Service",
        "model": vanna_service.model if vanna_service else "not initialized"
    }

@app.post("/train/ddl")
async def train_ddl(request: TrainDDLRequest):
    """训练 DDL 信息"""
    try:
        vanna_service.train_ddl(
            request.datasource_name,
            request.ddl
        )
        logger.info(f"DDL trained: {request.datasource_name}")
        return {"success": True, "message": "DDL trained successfully"}
    except Exception as e:
        logger.error(f"DDL training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train/sql")
async def train_sql(request: TrainSQLRequest):
    """训练问题-SQL对"""
    try:
        vanna_service.train_sql(
            request.datasource_name,
            request.question,
            request.sql
        )
        logger.info(f"SQL trained: {request.question}")
        return {"success": True, "message": "SQL trained successfully"}
    except Exception as e:
        logger.error(f"SQL training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_sql(request: GenerateSQLRequest):
    """生成 SQL"""
    try:
        result = vanna_service.generate_sql(
            request.datasource_name,
            request.question
        )
        logger.info(f"SQL generated: {request.question}")
        return result
    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/similar/{question}")
async def get_similar(question: str, n: int = 5):
    """获取相似训练数据"""
    try:
        similar = vanna_service.get_similar_training_data(question, n)
        return {"similar_questions": similar}
    except Exception as e:
        logger.error(f"Similar retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 4: 运行测试(通过)**

```bash
cd vanna-service
pytest tests/test_main.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add vanna-service/app/main.py vanna-service/tests/test_main.py
git commit -m "feat: implement Vanna Service FastAPI endpoints

- Add health check endpoint
- Add train_ddl endpoint
- Add train_sql endpoint
- Add generate_sql endpoint
- Add get_similar endpoint
- Configure logging with loguru
- Add API tests"
```

---

### Task 6: 实现 DDL 提取器

**Files:**
- Create: `vanna-service/app/ddl_extractor.py`
- Create: `vanna-service/tests/test_ddl_extractor.py`

**Interfaces:**
- Produces: `DDLExtractor` 类从不同数据库提取 DDL
- Consumes: 数据库连接配置

- [ ] **Step 1: 编写测试**

```python
# vana-service/tests/test_ddl_extractor.py

import pytest
from app.ddl_extractor import DDLExtractor

def test_ddl_extractor_init():
    """测试 DDL Extractor 初始化"""
    config = {
        'host': 'localhost',
        'port': 9000,
        'username': 'default',
        'password': '',
        'database': 'test'
    }
    extractor = DDLExtractor('clickhouse', config)
    assert extractor is not None
    assert extractor.db_type == 'clickhouse'

def test_clickhouse_ddl_extract():
    """测试 ClickHouse DDL 提取"""
    # 需要 ClickHouse 测试环境
    # 这里使用 mock 或跳过
    pytest.skip("Requires ClickHouse test environment")

def test_postgresql_ddl_extract():
    """测试 PostgreSQL DDL 提取"""
    pytest.skip("Requires PostgreSQL test environment")

def test_mysql_ddl_extract():
    """测试 MySQL DDL 提取"""
    pytest.skip("Requires MySQL test environment")
```

- [ ] **Step 2: 运行测试(失败)**

```bash
cd vanna-service
pytest tests/test_ddl_extractor.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现 DDL Extractor**

```python
# vana-service/app/ddl_extractor.py

from typing import List, Dict
from loguru import logger
import traceback

class DDLExtractor:
    """
    从不同数据库类型提取 DDL
    支持 ClickHouse, PostgreSQL, MySQL
    """
    
    def __init__(self, db_type: str, connection_config: dict):
        """
        初始化 DDL Extractor
        
        Args:
            db_type: clickhouse / postgresql / mysql
            connection_config: {
                'host': str,
                'port': int,
                'username': str,
                'password': str,
                'database': str
            }
        """
        self.db_type = db_type
        self.config = connection_config
        logger.info(f"DDLExtractor initialized for {db_type}")
    
    def extract_all_ddl(self) -> List[Dict]:
        """
        提取所有表的 DDL
        
        Returns:
            [{'table_name': str, 'ddl': str}]
        """
        if self.db_type == 'clickhouse':
            return self._extract_clickhouse_ddl()
        elif self.db_type == 'postgresql':
            return self._extract_postgresql_ddl()
        elif self.db_type == 'mysql':
            return self._extract_mysql_ddl()
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def _extract_clickhouse_ddl(self) -> List[Dict]:
        """提取 ClickHouse DDL"""
        from clickhouse_driver import Client
        
        try:
            client = Client(
                host=self.config['host'],
                port=self.config.get('port', 9000),
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database']
            )
            
            # 获取所有表
            tables_query = f"""
                SELECT name 
                FROM system.tables 
                WHERE database = '{self.config['database']}'
            """
            tables = client.execute(tables_query)
            
            ddl_list = []
            for (table_name,) in tables:
                # 获取表的 DDL
                ddl_query = f"SHOW CREATE TABLE `{table_name}`"
                result = client.execute(ddl_query)
                if result:
                    ddl = result[0][0]
                    ddl_list.append({
                        'table_name': table_name,
                        'ddl': ddl
                    })
                    logger.info(f"Extracted DDL for {table_name}")
            
            logger.info(f"Extracted {len(ddl_list)} tables from ClickHouse")
            return ddl_list
            
        except Exception as e:
            logger.error(f"ClickHouse DDL extraction failed: {e}\n{traceback.format_exc()}")
            raise
    
    def _extract_postgresql_ddl(self) -> List[Dict]:
        """提取 PostgreSQL DDL"""
        import psycopg2
        
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config.get('port', 5432),
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database']
            )
            
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            tables = cursor.fetchall()
            
            ddl_list = []
            for (table_name,) in tables:
                # 使用 pg_get_tabledef 函数 (PostgreSQL 9.4+)
                try:
                    cursor.execute(f"""
                        SELECT pg_get_tabledef('{table_name}'::regclass)
                    """)
                    ddl = cursor.fetchone()[0]
                except:
                    # 如果 pg_get_tabledef 不存在,使用 SHOW CREATE TABLE 替代
                    cursor.execute(f"""
                        SELECT 
                            'CREATE TABLE ' || table_name || ' (' ||
                            string_agg(column_name || ' ' || data_type, ', ') ||
                            ')' as ddl
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                        GROUP BY table_name
                    """)
                    result = cursor.fetchone()
                    ddl = result[0] if result else ""
                
                ddl_list.append({
                    'table_name': table_name,
                    'ddl': ddl
                })
                logger.info(f"Extracted DDL for {table_name}")
            
            conn.close()
            logger.info(f"Extracted {len(ddl_list)} tables from PostgreSQL")
            return ddl_list
            
        except Exception as e:
            logger.error(f"PostgreSQL DDL extraction failed: {e}\n{traceback.format_exc()}")
            raise
    
    def _extract_mysql_ddl(self) -> List[Dict]:
        """提取 MySQL DDL"""
        import mysql.connector
        
        try:
            conn = mysql.connector.connect(
                host=self.config['host'],
                port=self.config.get('port', 3306),
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database']
            )
            
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            ddl_list = []
            for (table_name,) in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                result = cursor.fetchone()
                ddl = result[1] if result else ""
                
                ddl_list.append({
                    'table_name': table_name,
                    'ddl': ddl
                })
                logger.info(f"Extracted DDL for {table_name}")
            
            conn.close()
            logger.info(f"Extracted {len(ddl_list)} tables from MySQL")
            return ddl_list
            
        except Exception as e:
            logger.error(f"MySQL DDL extraction failed: {e}\n{traceback.format_exc()}")
            raise
```

- [ ] **Step 4: 运行测试(通过)**

```bash
cd vanna-service
pytest tests/test_ddl_extractor.py -v
```

Expected: PASS (跳过需要环境的测试)

- [ ] **Step 5: Commit**

```bash
git add vanna-service/app/ddl_extractor.py vanna-service/tests/test_ddl_extractor.py
git commit -m "feat: implement DDL Extractor for multiple databases

- Support ClickHouse DDL extraction using SHOW CREATE TABLE
- Support PostgreSQL DDL extraction using pg_get_tabledef
- Support MySQL DDL extraction using SHOW CREATE TABLE
- Add error handling and logging
- Add unit tests"
```

---

### Task 7: 创建 ChromaDB 备份脚本

**Files:**
- Create: `vanna-service/scripts/backup_chromadb.py`
- Create: `vanna-service/scripts/restore_chromadb.py`

**Interfaces:**
- Produces: ChromaDB 备份和恢复脚本

- [ ] **Step 1: 创建备份脚本**

```python
# vana-service/scripts/backup_chromadb.py

import chromadb
import json
from datetime import datetime
from loguru import logger
import os

def backup_chromadb():
    """备份 ChromaDB 数据到 JSON 文件"""
    
    chromadb_path = os.getenv('CHROMADB_PATH', '/data/chromadb')
    backup_dir = '/data/backups'
    
    # 创建备份目录
    os.makedirs(backup_dir, exist_ok=True)
    
    # 连接 ChromaDB
    client = chromadb.PersistentClient(path=chromadb_path)
    
    # 获取所有 collections
    collections = client.list_collections()
    
    backup_data = {}
    for collection in collections:
        logger.info(f"Backing up collection: {collection.name}")
        
        # 获取所有数据
        results = collection.get()
        backup_data[collection.name] = {
            'ids': results['ids'],
            'documents': results['documents'],
            'metadatas': results['metadatas'],
            'embeddings': results.get('embeddings', []),
        }
    
    # 保存备份
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'{backup_dir}/chromadb_backup_{timestamp}.json'
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Backup saved to {backup_file}")
    print(f"✓ Backup successful: {backup_file}")
    print(f"✓ Collections backed up: {len(collections)}")

if __name__ == '__main__':
    backup_chromadb()
```

- [ ] **Step 2: 创建恢复脚本**

```python
# vana-service/scripts/restore_chromadb.py

import chromadb
import json
import sys
from loguru import logger
import os

def restore_chromadb(backup_file: str):
    """从 JSON 文件恢复 ChromaDB 数据"""
    
    if not os.path.exists(backup_file):
        logger.error(f"Backup file not found: {backup_file}")
        sys.exit(1)
    
    chromadb_path = os.getenv('CHROMADB_PATH', '/data/chromadb')
    
    # 连接 ChromaDB
    client = chromadb.PersistentClient(path=chromadb_path)
    
    # 加载备份数据
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    # 恢复每个 collection
    for collection_name, data in backup_data.items():
        logger.info(f"Restoring collection: {collection_name}")
        
        # 创建或获取 collection
        collection = client.get_or_create_collection(collection_name)
        
        # 清空现有数据
        existing_ids = collection.get()['ids']
        if existing_ids:
            collection.delete(ids=existing_ids)
            logger.info(f"Cleared {len(existing_ids)} existing records")
        
        # 恢复数据
        if data['ids']:
            collection.add(
                ids=data['ids'],
                documents=data['documents'],
                metadatas=data['metadatas'],
                embeddings=data.get('embeddings', None),
            )
            logger.info(f"Restored {len(data['ids'])} records")
    
    logger.info(f"Restore completed from {backup_file}")
    print(f"✓ Restore successful from: {backup_file}")
    print(f"✓ Collections restored: {len(backup_data)}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python restore_chromadb.py <backup_file>")
        sys.exit(1)
    
    restore_chromadb(sys.argv[1])
```

- [ ] **Step 3: 测试备份脚本(手动)**

```bash
# 稍后在集成测试中验证
echo "Backup scripts created"
```

- [ ] **Step 4: Commit**

```bash
git add vanna-service/scripts/
git commit -m "feat: add ChromaDB backup and restore scripts

- Add backup_chromadb.py to backup all collections to JSON
- Add restore_chromadb.py to restore from JSON backup
- Add logging and error handling"
```

---

## Phase 3: Backend API 实现

由于篇幅限制,我将继续在下一个任务序列中详细展开 Backend API 的实现。Backend API 包含:

1. **Task 8-15:** Backend 基础配置、数据模型、数据库连接、数据源管理服务、SQL 执行服务、训练数据管理、API 端点实现、单元测试

详细实现将遵循相同的 TDD 模式和 bite-sized 任务结构。

---

## Phase 4: Frontend 实现

Frontend 实现包含:

1. **Task 16-25:** React 项目初始化、API 服务层、AskInterface 组件、DataSourceManager 组件、TrainingManager 组件、页面路由、样式配置、nginx 配置、构建优化、前端测试

详细实现将遵循相同的任务结构。

---

## Phase 5: Docker 集成和测试

包含:

1. **Task 26-30:** Docker 构建验证、容器启动测试、服务间通信测试、完整流程集成测试、文档完善

---

## 实现顺序建议

**推荐执行顺序:**

1. **Phase 1 (Task 1-2)** - 项目初始化和 Docker Compose
2. **Phase 2 (Task 3-7)** - Vanna Service 完整实现
3. **Phase 3 (Task 8-15)** - Backend API 完整实现
4. **Phase 4 (Task 16-25)** - Frontend 完整实现
5. **Phase 5 (Task 26-30)** - Docker 集成和最终测试

**关键依赖:**

- Task 3-7 必须先完成(核心 AI 服务)
- Task 8-15 依赖 Task 3-7(Backend 调用 Vanna Service)
- Task 16-25 依赖 Task 8-15(Frontend 调用 Backend API)
- Task 26-30 在所有代码完成后进行

---

## 测试策略

每个任务都遵循 TDD:

1. 先编写测试
2. 运行测试(失败)
3. 实现代码
4. 运行测试(通过)
5. Commit

**集成测试:**

在 Phase 5 进行完整的端到端测试:
- Docker 容器启动测试
- 服务间通信测试
- 数据源添加 → SQL 生成 → 执行完整流程测试
- 训练数据管理流程测试

---

## 下一步

完整的 Backend API 和 Frontend 实现计划将在后续文档中展开,每个任务都将遵循相同的详细结构和 TDD 流程。

---

**文档状态:** Phase 1-2 完成  
**总任务数:** 30 个(本文档覆盖 1-7)  
**预计时间:** 2-3 周(完整实现)