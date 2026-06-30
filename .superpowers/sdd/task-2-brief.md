# Task 2: 创建 Docker Compose 配置

## 任务描述

创建 docker-compose.yml 文件，定义所有服务的配置，包括 frontend、backend-api、vanna-service 和 postgres。

## 文件清单

需要创建的文件：
- `docker-compose.yml`

## 接口定义

此任务产生：`docker-compose.yml` 定义所有服务配置
此任务消费：`.env` 文件中的环境变量（通过 ${MINIMAX_API_KEY}）

## Global Constraints

必须遵循以下全局约束：
- MiniMax endpoint: `10.242.52.62:9924`（在 docker-compose.yml 中设置）
- MiniMax model: `MiniMax-M2.7`（在 docker-compose.yml 中设置）
- SQL 执行超时: 60 秒（在 backend-api 环境变量中设置）
- 最大返回行数: 1000 行（在 backend-api 环境变量中设置）
- ChromaDB 持久化路径: `/data/chromadb`（在 vanna-service 环境变量中设置）
- PostgreSQL 连接: `postgresql://text2sql:text2sql123@postgres:5432/text2sql`
- API Key 从 `.env` 文件读取，不硬编码在 docker-compose.yml 中

## 实现步骤

### Step 1: 创建 docker-compose.yml

创建包含以下内容的 docker-compose.yml 文件：

```yaml
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
```

### Step 2: 验证 docker-compose.yml

运行以下命令验证配置文件语法：

```bash
docker-compose config
```

Expected: 显示配置详情，无错误

### Step 3: Commit

```bash
git add docker-compose.yml
git commit -m "feat: add docker-compose configuration

- Define 4 services: frontend, backend-api, vanna-service, postgres
- Configure volumes for ChromaDB and PostgreSQL
- Configure health checks
- Set up internal network"
```

## 上下文说明

这是项目的第二个任务，定义了所有服务的容器配置。这个配置是后续实现的基础：
- Task 3-7 会实现 Vanna Service（对应 vanna-service 容器）
- Task 8-15 会实现 Backend API（对应 backend-api 容器）
- Task 16-25 会实现 Frontend（对应 frontend 容器）

## 关键配置说明

1. **frontend**: React 前端服务
   - 端口 3000
   - 依赖 backend-api

2. **backend-api**: FastAPI 后端服务
   - 端口 8000
   - 连接 postgres 和 vanna-service
   - 健康检查

3. **vanna-service**: Vanna AI 服务
   - 端口 8001
   - MiniMax API Key 从环境变量读取
   - ChromaDB 数据持久化

4. **postgres**: PostgreSQL 数据库
   - 端口 5432
   - 持久化元数据

## 报告要求

完成后，请在 `/Users/owen/coding/2026-自学/Text2Sql/.superpowers/sdd/task-2-report.md` 文件中编写报告，包含：
1. 执行的步骤
2. docker-compose config 验证结果
3. Commit hash
4. 任何发现的问题或关注点
5. 返回状态（DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED）