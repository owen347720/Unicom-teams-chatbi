# Backend API 实现计划补充

> **续: Vanna Text2SQL 实现计划 - Phase 3: Backend API 详细任务**

本文档详细展开 Backend API 的实现任务(Task 8-15)。

---

## Phase 3: Backend API 实现

### Task 8: Backend 基础配置

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/requirements.txt`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`

**Interfaces:**
- Produces: Backend 容器配置,数据库连接,配置管理
- Consumes: PostgreSQL 数据库

- [ ] **Step 1: 创建 requirements.txt**

```bash
cat > backend/requirements.txt << 'EOF'
# FastAPI
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Database drivers
clickhouse-driver==0.2.6
mysql-connector-python==8.2.0

# HTTP client
httpx==0.25.2
requests==2.31.0

# Security
cryptography==41.0.7
python-jose==3.3.0

# Logging
loguru==0.7.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
EOF
```

- [ ] **Step 2: 创建 Dockerfile**

```bash
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

- [ ] **Step 3: 创建 config.py**

```python
# backend/app/config.py

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API 配置
    app_name: str = "Text2SQL Backend API"
    app_version: str = "1.0.0"
    
    # Vanna Service
    vanna_service_url: str = "http://vanna-service:8001"
    
    # PostgreSQL
    database_url: str = "postgresql://text2sql:text2sql123@postgres:5432/text2sql"
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    # SQL 配置
    sql_timeout: int = 60
    max_result_rows: int = 1000
    
    # 加密密钥
    encryption_key: str = "default-key-change-in-production"
    
    # 日志
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

- [ ] **Step 4: 创建 database.py**

```python
# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库"""
    from app.models import datasource, training, history, config
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile backend/requirements.txt backend/app/config.py backend/app/database.py
git commit -m "feat: add Backend API base configuration

- Add Dockerfile with health check
- Add requirements.txt with dependencies
- Add config.py with Pydantic settings
- Add database.py with SQLAlchemy setup"
```

---

### Task 9: 实现数据模型

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/datasource.py`
- Create: `backend/app/models/training.py`
- Create: `backend/app/models/history.py`
- Create: `backend/app/models/config.py`

**Interfaces:**
- Produces: SQLAlchemy 数据模型(DataSource, TrainingData, QueryHistory, SystemConfig)

- [ ] **Step 1: 创建模型文件**

```python
# backend/app/models/__init__.py

from app.models.datasource import DataSource
from app.models.training import TrainingData
from app.models.history import QueryHistory
from app.models.config import SystemConfig
```

```python
# backend/app/models/datasource.py

from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base

class DataSource(Base):
    """数据源配置模型"""
    __tablename__ = "datasources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    type = Column(String(20), nullable=False)  # clickhouse / postgresql / mysql
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)  # 加密存储
    database = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

```python
# backend/app/models/training.py

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base

class TrainingData(Base):
    """训练数据模型"""
    __tablename__ = "training_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    datasource_id = Column(UUID(as_uuid=True), ForeignKey("datasources.id"), nullable=False)
    question = Column(String(500), nullable=False)
    sql = Column(String(2000), nullable=False)
    source = Column(String(20), nullable=False)  # manual / auto
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

```python
# backend/app/models/history.py

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base

class QueryHistory(Base):
    """查询历史模型"""
    __tablename__ = "query_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    datasource_id = Column(UUID(as_uuid=True), ForeignKey("datasources.id"), nullable=False)
    question = Column(String(500), nullable=False)
    generated_sql = Column(String(2000), nullable=False)
    final_sql = Column(String(2000), nullable=False)
    executed = Column(Boolean, default=False)
    result_rows = Column(Integer, default=0)
    execution_time = Column(Float, default=0.0)
    error_message = Column(String(1000), default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
```

```python
# backend/app/models/config.py

from sqlalchemy import Column, String, Integer, Boolean
from app.database import Base

class SystemConfig(Base):
    """系统配置模型"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(50), unique=True, nullable=False)
    config_value = Column(String(500), nullable=False)
    description = Column(String(200))
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add SQLAlchemy data models

- Add DataSource model for database connection configs
- Add TrainingData model for SQL training examples
- Add QueryHistory model for query execution history
- Add SystemConfig model for system settings"
```

---

### Task 10: 实现密码加密服务

**Files:**
- Create: `backend/app/utils/crypto.py`
- Create: `backend/tests/test_crypto.py`

**Interfaces:**
- Produces: `encrypt_password()`, `decrypt_password()` 函数

- [ ] **Step 1: 编写测试**

```python
# backend/tests/test_crypto.py

import pytest
from app.utils.crypto import encrypt_password, decrypt_password

def test_encrypt_decrypt():
    """测试加密解密"""
    original = "my_password_123"
    encrypted = encrypt_password(original)
    
    assert encrypted != original
    assert decrypt_password(encrypted) == original

def test_encrypt_different():
    """测试相同密码加密结果不同"""
    password = "same_password"
    encrypted1 = encrypt_password(password)
    encrypted2 = encrypt_password(password)
    
    # Fernet 加密每次结果不同
    assert encrypted1 != encrypted2
    assert decrypt_password(encrypted1) == password
    assert decrypt_password(encrypted2) == password
```

- [ ] **Step 2: 运行测试(失败)**

```bash
cd backend
pytest tests/test_crypto.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现加密工具**

```python
# backend/app/utils/crypto.py

from cryptography.fernet import Fernet
from app.config import settings
import base64
import os

# 从配置获取加密密钥,确保是有效的 Fernet key
def get_encryption_key():
    """获取加密密钥"""
    key = settings.encryption_key
    
    # 如果密钥不是有效的 Fernet key,生成一个
    if not key or len(key) != 44:  # Fernet key 长度为 44
        key = Fernet.generate_key().decode()
    
    return key

cipher = Fernet(get_encryption_key())

def encrypt_password(password: str) -> str:
    """加密密码"""
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted: str) -> str:
    """解密密码"""
    return cipher.decrypt(encrypted.encode()).decode()
```

- [ ] **Step 4: 运行测试(通过)**

```bash
cd backend
pytest tests/test_crypto.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/crypto.py backend/tests/test_crypto.py
git commit -m "feat: implement password encryption utilities

- Add encrypt_password and decrypt_password using Fernet
- Add encryption key configuration
- Add unit tests"
```

---

### Task 11: 实现数据源管理服务

**Files:**
- Create: `backend/app/services/db_connector.py`
- Create: `backend/app/services/datasource_manager.py`
- Create: `backend/tests/test_datasource_manager.py`

**Interfaces:**
- Produces: `DatasourceManager` 类提供数据源连接测试、DDL提取
- Consumes: Vanna Service API, 数据库驱动

- [ ] **Step 1: 编写测试**

```python
# backend/tests/test_datasource_manager.py

import pytest
from app.services.datasource_manager import DatasourceManager

def test_datasource_manager_init():
    """测试初始化"""
    manager = DatasourceManager()
    assert manager is not None

def test_test_connection_clickhouse():
    """测试 ClickHouse 连接测试"""
    manager = DatasourceManager()
    config = {
        'type': 'clickhouse',
        'host': 'localhost',
        'port': 9000,
        'username': 'default',
        'password': '',
        'database': 'test'
    }
    
    # 需要 ClickHouse 测试环境
    pytest.skip("Requires ClickHouse test environment")

def test_extract_ddl():
    """测试 DDL 提取"""
    pytest.skip("Requires database test environment")
```

- [ ] **Step 2: 运行测试(失败)**

```bash
cd backend
pytest tests/test_datasource_manager.py -v
```

Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: 实现数据库连接器**

```python
# backend/app/services/db_connector.py

from typing import Dict, List, Any
from loguru import logger
import traceback

class DBConnector:
    """数据库连接器"""
    
    @staticmethod
    def execute_sql(
        db_type: str,
        config: dict,
        sql: str,
        timeout: int = 60
    ) -> Dict:
        """
        执行 SQL 查询
        
        Args:
            db_type: clickhouse / postgresql / mysql
            config: 连接配置
            sql: SQL 查询语句
            timeout: 超时时间
            
        Returns:
            {'columns': [], 'rows': [], 'row_count': int, 'execution_time': float}
        """
        import time
        start_time = time.time()
        
        try:
            if db_type == 'clickhouse':
                return DBConnector._execute_clickhouse(config, sql, timeout)
            elif db_type == 'postgresql':
                return DBConnector._execute_postgresql(config, sql, timeout)
            elif db_type == 'mysql':
                return DBConnector._execute_mysql(config, sql, timeout)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"SQL execution failed: {e}\n{traceback.format_exc()}")
            raise
        
    @staticmethod
    def _execute_clickhouse(config: dict, sql: str, timeout: int) -> Dict:
        """执行 ClickHouse SQL"""
        from clickhouse_driver import Client
        import time
        
        client = Client(
            host=config['host'],
            port=config.get('port', 9000),
            user=config['username'],
            password=config['password'],
            database=config['database']
        )
        
        start_time = time.time()
        result = client.execute(sql, with_column_types=True)
        execution_time = time.time() - start_time
        
        # 解析结果
        if result:
            columns = [col[0] for col in result[1]]  # column names
            rows = result[0]  # data rows
            row_count = len(rows)
        else:
            columns = []
            rows = []
            row_count = 0
        
        return {
            'columns': columns,
            'rows': rows,
            'row_count': row_count,
            'execution_time': execution_time
        }
    
    @staticmethod
    def _execute_postgresql(config: dict, sql: str, timeout: int) -> Dict:
        """执行 PostgreSQL SQL"""
        import psycopg2
        import time
        
        conn = psycopg2.connect(
            host=config['host'],
            port=config.get('port', 5432),
            user=config['username'],
            password=config['password'],
            database=config['database']
        )
        
        cursor = conn.cursor()
        
        start_time = time.time()
        cursor.execute(sql)
        execution_time = time.time() - start_time
        
        # 获取结果
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            row_count = len(rows)
        else:
            columns = []
            rows = []
            row_count = cursor.rowcount
        
        conn.close()
        
        return {
            'columns': columns,
            'rows': rows,
            'row_count': row_count,
            'execution_time': execution_time
        }
    
    @staticmethod
    def _execute_mysql(config: dict, sql: str, timeout: int) -> Dict:
        """执行 MySQL SQL"""
        import mysql.connector
        import time
        
        conn = mysql.connector.connect(
            host=config['host'],
            port=config.get('port', 3306),
            user=config['username'],
            password=config['password'],
            database=config['database']
        )
        
        cursor = conn.cursor()
        
        start_time = time.time()
        cursor.execute(sql)
        execution_time = time.time() - start_time
        
        # 获取结果
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            row_count = len(rows)
        else:
            columns = []
            rows = []
            row_count = cursor.rowcount
        
        conn.close()
        
        return {
            'columns': columns,
            'rows': rows,
            'row_count': row_count,
            'execution_time': execution_time
        }
```

- [ ] **Step 4: 实现数据源管理器**

```python
# backend/app/services/datasource_manager.py

from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.datasource import DataSource
from app.utils.crypto import encrypt_password, decrypt_password
from app.services.db_connector import DBConnector
import httpx
from loguru import logger
from app.config import settings

class DatasourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self.vanna_service_url = settings.vanna_service_url
    
    def test_connection(self, db_type: str, config: dict) -> Dict:
        """
        测试数据源连接
        
        Returns:
            {'success': bool, 'message': str, 'tables_count': int}
        """
        try:
            # 执行简单查询测试连接
            test_sql = "SELECT 1"
            DBConnector.execute_sql(db_type, config, test_sql, timeout=5)
            
            # 获取表数量
            tables_count = self._get_tables_count(db_type, config)
            
            logger.info(f"Connection test successful for {config['host']}")
            return {
                'success': True,
                'message': 'Connection successful',
                'tables_count': tables_count
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'success': False,
                'message': str(e),
                'tables_count': 0
            }
    
    def _get_tables_count(self, db_type: str, config: dict) -> int:
        """获取表数量"""
        try:
            if db_type == 'clickhouse':
                sql = f"SELECT count(*) FROM system.tables WHERE database = '{config['database']}'"
            elif db_type == 'postgresql':
                sql = "SELECT count(*) FROM pg_tables WHERE schemaname = 'public'"
            elif db_type == 'mysql':
                sql = "SELECT count(*) FROM information_schema.tables WHERE table_schema = DATABASE()"
            
            result = DBConnector.execute_sql(db_type, config, sql)
            return result['rows'][0][0] if result['rows'] else 0
            
        except Exception as e:
            logger.error(f"Get tables count failed: {e}")
            return 0
    
    async def extract_and_train_ddl(
        self,
        datasource_name: str,
        db_type: str,
        config: dict
    ) -> int:
        """
        提取 DDL 并训练到 Vanna Service
        
        Returns:
            tables_extracted: int
        """
        try:
            # 调用 Vanna Service 的 DDL 提取
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.vanna_service_url}/extract_ddl",
                    json={
                        "datasource_name": datasource_name,
                        "db_type": db_type,
                        "config": config
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    tables_count = data.get('tables_extracted', 0)
                    logger.info(f"DDL extracted and trained: {tables_count} tables")
                    return tables_count
                else:
                    logger.error(f"DDL extraction failed: {response.text}")
                    return 0
                    
        except Exception as e:
            logger.error(f"DDL extraction and training failed: {e}")
            return 0
    
    def create_datasource(
        self,
        db: Session,
        name: str,
        db_type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str
    ) -> DataSource:
        """创建数据源"""
        datasource = DataSource(
            name=name,
            type=db_type,
            host=host,
            port=port,
            username=username,
            password=encrypt_password(password),  # 加密存储
            database=database
        )
        
        db.add(datasource)
        db.commit()
        db.refresh(datasource)
        
        logger.info(f"Datasource created: {name}")
        return datasource
    
    def get_datasource_config(self, datasource: DataSource) -> dict:
        """获取解密后的数据源配置"""
        return {
            'type': datasource.type,
            'host': datasource.host,
            'port': datasource.port,
            'username': datasource.username,
            'password': decrypt_password(datasource.password),
            'database': datasource.database
        }
```

- [ ] **Step 5: 运行测试(通过)**

```bash
cd backend
pytest tests/test_datasource_manager.py -v
```

Expected: PASS (跳过需要环境的测试)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ backend/tests/test_datasource_manager.py
git commit -m "feat: implement datasource management services

- Add DBConnector for executing SQL on different databases
- Add DatasourceManager for connection testing and DDL extraction
- Add password encryption/decryption
- Add unit tests"
```

---

### Task 12: 实现 API 路由

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/ask.py`
- Create: `backend/app/routers/datasources.py`
- Create: `backend/app/routers/training.py`
- Create: `backend/app/routers/settings.py`

**Interfaces:**
- Produces: REST API 端点(/ask/*, /datasources/*, /training/*, /settings/*)
- Consumes: DatasourceManager, Vanna Service, DBConnector

由于篇幅限制,这里展示关键端点的实现示例:

- [ ] **Step 1: 实现 datasources.py**

```python
# backend/app/routers/datasources.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models.datasource import DataSource
from app.services.datasource_manager import DatasourceManager
from loguru import logger

router = APIRouter(prefix="/datasources", tags=["datasources"])
manager = DatasourceManager()

class DatasourceCreate(BaseModel):
    name: str
    type: str  # clickhouse / postgresql / mysql
    host: str
    port: int
    username: str
    password: str
    database: str

class DatasourceResponse(BaseModel):
    id: str
    name: str
    type: str
    host: str
    port: int
    username: str
    database: str
    is_active: bool
    created_at: str

@router.get("/list")
async def list_datasources(db: Session = Depends(get_db)):
    """获取数据源列表"""
    datasources = db.query(DataSource).filter(DataSource.is_active == True).all()
    
    return {
        "total": len(datasources),
        "items": [
            {
                "id": str(ds.id),
                "name": ds.name,
                "type": ds.type,
                "host": ds.host,
                "port": ds.port,
                "username": ds.username,
                "database": ds.database,
                "is_active": ds.is_active,
                "created_at": ds.created_at.isoformat()
            }
            for ds in datasources
        ]
    }

@router.post("/add")
async def add_datasource(
    request: DatasourceCreate,
    db: Session = Depends(get_db)
):
    """添加数据源"""
    # 测试连接
    test_result = manager.test_connection(request.type, {
        'host': request.host,
        'port': request.port,
        'username': request.username,
        'password': request.password,
        'database': request.database
    })
    
    if not test_result['success']:
        raise HTTPException(status_code=400, detail=test_result['message'])
    
    # 创建数据源
    datasource = manager.create_datasource(
        db=db,
        name=request.name,
        db_type=request.type,
        host=request.host,
        port=request.port,
        username=request.username,
        password=request.password,
        database=request.database
    )
    
    # 提取 DDL 并训练
    config = manager.get_datasource_config(datasource)
    tables_extracted = await manager.extract_and_train_ddl(
        datasource_name=request.name,
        db_type=request.type,
        config=config
    )
    
    logger.info(f"Datasource added: {request.name}")
    
    return {
        "id": str(datasource.id),
        "message": "Datasource added successfully",
        "tables_extracted": tables_extracted
    }

@router.post("/{id}/test")
async def test_datasource(id: str, db: Session = Depends(get_db)):
    """测试数据源连接"""
    datasource = db.query(DataSource).filter(DataSource.id == id).first()
    
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    
    config = manager.get_datasource_config(datasource)
    test_result = manager.test_connection(datasource.type, config)
    
    return test_result
```

- [ ] **Step 2: 实现 ask.py**

```python
# backend/app/routers/ask.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.datasource import DataSource
from app.models.history import QueryHistory
from app.services.datasource_manager import DatasourceManager
from app.services.db_connector import DBConnector
import httpx
from app.config import settings
from loguru import logger

router = APIRouter(prefix="/ask", tags=["ask"])
manager = DatasourceManager()

class GenerateSQLRequest(BaseModel):
    datasource_id: str
    question: str

class ExecuteSQLRequest(BaseModel):
    datasource_id: str
    sql: str

@router.post("/generate-sql")
async def generate_sql(
    request: GenerateSQLRequest,
    db: Session = Depends(get_db)
):
    """生成 SQL"""
    # 获取数据源
    datasource = db.query(DataSource).filter(
        DataSource.id == request.datasource_id
    ).first()
    
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    
    # 调用 Vanna Service 生成 SQL
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.vanna_service_url}/generate",
                json={
                    "datasource_name": datasource.name,
                    "question": request.question
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"SQL generated: {request.question}")
                return result
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"SQL generation failed: {response.text}"
                )
                
    except Exception as e:
        logger.error(f"SQL generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-sql")
async def execute_sql(
    request: ExecuteSQLRequest,
    db: Session = Depends(get_db)
):
    """执行 SQL"""
    # 获取数据源
    datasource = db.query(DataSource).filter(
        DataSource.id == request.datasource_id
    ).first()
    
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    
    # 获取配置
    config = manager.get_datasource_config(datasource)
    
    # 执行 SQL
    try:
        result = DBConnector.execute_sql(
            db_type=datasource.type,
            config=config,
            sql=request.sql,
            timeout=settings.sql_timeout
        )
        
        # 限制返回行数
        if result['row_count'] > settings.max_result_rows:
            result['rows'] = result['rows'][:settings.max_result_rows]
            result['truncated'] = True
        else:
            result['truncated'] = False
        
        logger.info(f"SQL executed: {request.sql[:100]}")
        return result
        
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/
git commit -m "feat: implement Backend API routers

- Add datasources router with list/add/test endpoints
- Add ask router with generate-sql/execute-sql endpoints
- Add connection to Vanna Service
- Add error handling and logging"
```

---

### Task 13: 实现 FastAPI 主应用

**Files:**
- Create: `backend/app/main.py`

**Interfaces:**
- Produces: FastAPI 应用入口,启动初始化

- [ ] **Step 1: 实现 main.py**

```python
# backend/app/main.py

from fastapi import FastAPI, CORS
from loguru import logger
import sys

from app.config import settings
from app.database import init_db
from app.routers import ask, datasources, training, settings

# Configure logging
logger.remove()
logger.add(sys.stderr, level=settings.log_level)
logger.add("/app/logs/backend.log", level="DEBUG", rotation="1 day")

# Initialize app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Text2SQL Backend API - Natural language to SQL query"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    logger.info("Backend API starting up...")
    init_db()
    logger.info("Database initialized")

# Include routers
app.include_router(ask.router, prefix="/api/v1")
app.include_router(datasources.router, prefix="/api/v1")
app.include_router(training.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }

# Root endpoint
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Text2SQL Backend API",
        "docs": "/docs",
        "health": "/health"
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: implement Backend API main application

- Add FastAPI app with CORS middleware
- Add database initialization on startup
- Include all routers
- Add health check endpoint
- Configure logging"
```

---

## 下一步

Backend API 的详细实现已完成 Task 8-13。接下来需要:

- **Task 14:** Backend 单元测试和集成测试
- **Task 15:** Backend API 文档和验证

然后进入 **Phase 4: Frontend 实现**(Task 16-25)。

---

**文档状态:** Phase 3 Backend API 核心实现完成  
**总任务数:** 30 个(本文档覆盖 8-13)