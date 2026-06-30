# Task 3: 创建 Vanna Service 基础配置

## 任务描述

创建 Vanna Service 的基础配置文件，包括 Dockerfile、requirements.txt 和 config.py。这是 Vanna AI 服务的基础设施。

## 文件清单

需要创建的文件：
- `vanna-service/Dockerfile`
- `vanna-service/requirements.txt`
- `vanna-service/app/__init__.py`（空文件）
- `vanna-service/app/config.py`

## 接口定义

此任务产生：Vanna Service 容器配置和 Python 依赖
此任务为 Task 4-7 提供基础设施

## Global Constraints

必须遵循以下全局约束：
- MiniMax endpoint: `10.242.52.62:9924`（在 config.py 中默认设置）
- MiniMax model: `MiniMax-M2.7`（在 config.py 中默认设置）
- ChromaDB 持久化路径: `/data/chromadb`（在 config.py 中默认设置）
- Python 版本: 3.11
- 使用 Pydantic Settings 进行配置管理
- 使用 loguru 进行日志记录

## 实现步骤

### Step 1: 创建 requirements.txt

```bash
cat > vanna-service/requirements.txt << 'EOF'
# FastAPI
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

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

### Step 2: 创建 Dockerfile

```bash
cat > vanna-service/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create necessary directories
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

### Step 3: 创建 app/__init__.py

```bash
touch vanna-service/app/__init__.py
```

### Step 4: 创建 app/config.py

```python
# vana-service/app/config.py

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Vanna Service 配置"""
    
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

# 创建全局配置实例
settings = Settings()
```

### Step 5: 验证目录结构

```bash
ls -la vanna-service/
ls -la vanna-service/app/
```

### Step 6: Commit

```bash
git add vanna-service/
git commit -m "feat: add Vanna Service base configuration

- Add Dockerfile with Python 3.11 and health check
- Add requirements.txt with FastAPI, Vanna, ChromaDB dependencies
- Add config.py with Pydantic Settings for MiniMax and ChromaDB
- Create app directory structure"
```

## 关键依赖说明

**FastAPI** (0.104.1): 用于构建 REST API
**Vanna** (0.5.4): Text2SQL 框架核心
**ChromaDB** (0.4.22): 向量数据库，存储训练数据
**Pydantic Settings** (2.1.0): 配置管理，从环境变量读取
**Loguru** (0.7.2): 日志记录

## 配置说明

`config.py` 使用 Pydantic Settings：
- 默认值硬编码（minimax_endpoint、minimax_model、chromadb_path）
- minimax_api_key 从环境变量读取（必需）
- 支持从 .env 文件加载

## 上下文说明

这是 Vanna Service 的基础配置任务，后续任务会在此基础上实现：
- Task 4: 实现 VannaService 核心类
- Task 5: 实现 FastAPI 服务端点
- Task 6: 实现 DDL 提取器
- Task 7: 创建 ChromaDB 备份脚本

## 报告要求

完成后，请在 `/Users/owen/coding/2026-自学/Text2Sql/.superpowers/sdd/task-3-report.md` 编写报告，包含：
1. 执行的步骤
2. 目录结构验证结果
3. Commit hash
4. 任何问题或关注点
5. 返回状态（DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED）