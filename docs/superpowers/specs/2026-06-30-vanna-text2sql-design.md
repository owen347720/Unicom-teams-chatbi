# Vanna Text2SQL 问数系统设计文档

**日期：** 2026-06-30  
**项目：** Text2Sql - 团队内取数系统  
**目标：** 构建基于 Vanna 的 Text2SQL 问数极速开发原型

---

## 一、项目概述

### 1.1 项目目标
构建一个团队内取数项目，实现自然语言问数功能，所有服务容器化部署，支持数据源插拔，特别支持 ClickHouse 数据库。

最终交付物需要支持提供给其他组在他们的 A100 服务器上部署。目标服务器常规启动路径应只依赖 Docker 和 Docker Compose：加载已打包镜像、配置 `.env`、执行 `docker compose -f docker-compose.release.yml up -d` 即可启动完整系统。

### 1.2 核心特性
- 自然语言转 SQL 查询（基于 Vanna + MiniMax-M2.7）
- 前后端分离架构（React + FastAPI）
- 完全容器化部署（docker-compose 一键启动）
- Web UI 管理数据源（支持新增/编辑/删除）
- 支持主流数据库（ClickHouse、PostgreSQL、MySQL）
- 训练数据管理（手动添加 + 自动训练）
- 无用户认证（内部工具）

---

## 二、整体架构设计

### 2.1 系统架构图

```
┌─────────────┐
│  Frontend   │ React + TypeScript + Ant Design
│  (容器)      │ 提供问数界面、数据源管理、训练数据管理
└─────────────┘
       ↓ HTTP API
┌─────────────┐
│ Backend API │ FastAPI
│  (容器)      │ 业务逻辑、数据源连接、SQL执行、权限校验
└─────────────┘
       ↓ RPC/HTTP
┌─────────────┐
│ Vanna Service│ Vanna + ChromaDB + MiniMax-M2.7
│  (容器)      │ SQL生成、训练数据管理、向量检索
└─────────────┘
       ↓ SQL Connection
┌─────────────┐
│ 外部数据源   │ ClickHouse / PostgreSQL / MySQL
│(其他服务器)  │ 团队实际的业务数据库
└─────────────┘
```

### 2.2 技术栈选择

**前端：**
- React 18 + TypeScript
- Ant Design 5.x（ProComponents）
- Axios（API 请求）
- React Query（状态管理）
- Monaco Editor（SQL 编辑器）

**后端：**
- FastAPI（Python Web 框架）
- PostgreSQL（元数据存储）
- SQLAlchemy（ORM）

**AI 服务：**
- Vanna（Text2SQL 框架）
- ChromaDB（向量数据库）
- MiniMax-M2.7（LLM，OpenAI 兼容接口）
- Endpoint: 10.242.52.62:9924

**部署：**
- Docker + docker-compose
- 完全容器化部署
- Volume 持久化数据
- 支持离线/半离线镜像包交付到 A100 服务器
- Release compose 使用固定镜像 tag，不要求目标服务器具备源码构建环境

---

## 三、前端界面设计

### 3.1 页面结构

**1. 问数主界面**
```
├─ 数据源选择下拉框
├─ 问题输入框（自然语言）
├─ 生成的SQL预览（Monaco Editor，可编辑）
├─ SQL执行按钮
├─ 结果展示（Ant Design Table + 图表）
├─ 执行历史记录侧边栏
└─ "添加为训练数据"按钮（用户执行后）
```

**2. 数据源管理页面**
```
├─ 数据源列表（Ant Design Cards）
├─ 添加数据源按钮
├─ 数据源表单（Modal）
│  ├─ 数据源类型选择（ClickHouse/PostgreSQL/MySQL）
│  ├─ 连接配置（host、port、username、password、database）
│  ├─ 连接测试按钮
│  ├─ 表结构预览（可选）
└─ 编辑/删除数据源操作
```

**3. 训练数据管理页面**
```
├─ 训练数据列表（Ant Design Table）
│  ├─ 列：数据源、问题、SQL、来源、状态、时间
├─ 手动添加训练数据按钮
├─ 添加训练数据表单（Modal）
│  ├─ 选择数据源
│  ├─ 输入问题
│  ├─ 输入 SQL 示例
├─ 待审核训练数据列表（自动训练）
├─ 审核/编辑/删除操作
└─ 批量导入训练数据（可选）
```

**4. 系统设置页面（可选）**
```
├─ MiniMax API 配置
│  ├─ Endpoint（默认：10.242.52.62:9924）
│  ├─ Model（默认：MiniMax-M2.7）
│  ├─ API Key（加密存储）
└─ 其他参数调整（超时时间、结果限制等）
```

### 3.2 关键交互流程

**问数流程：**
```
用户输入问题 → 选择数据源
→ 点击"生成SQL"
→ 前端显示生成的SQL（可编辑）
→ 用户确认或修改SQL
→ 点击"执行"
→ 显示结果表格/图表
→ 用户可选择"添加为训练数据"
```

**数据源添加流程：**
```
点击"添加数据源" → 填写表单 → 点击"测试连接"
→ 连接成功 → 点击"保存"
→ 系统自动提取表结构（DDL）→ 存入向量库
→ 数据源列表显示新数据源
```

---

## 四、后端 API 设计

### 4.1 API 端点设计

```
/api/v1/
├─ /ask/
│  ├─ POST /generate-sql        # 生成SQL（不执行）
│  │  Request: {datasource_id, question}
│  │  Response: {sql, related_training_data}
│  ├─ POST /execute-sql         # 执行SQL并返回结果
│  │  Request: {datasource_id, sql}
│  │  Response: {columns, rows, row_count, execution_time}
│  └─ GET  /history             # 查询历史记录
│     Response: [{id, question, sql, executed, created_at}]
│
├─ /datasources/
│  ├─ GET  /list                # 获取所有数据源
│  │  Response: [{id, name, type, host, database, is_active}]
│  ├─ POST /add                 # 添加新数据源
│  │  Request: {name, type, host, port, username, password, database}
│  │  Response: {id, message, tables_extracted}
│  ├─ PUT  /{id}                # 更新数据源配置
│  ├─ DELETE /{id}              # 删除数据源
│  ├─ POST /{id}/test           # 测试数据源连接
│  │  Response: {success, message, tables_count}
│  ├─ GET  /{id}/tables         # 获取表结构列表
│  │  Response: [{table_name, columns, row_count}]
│  └─ GET  /{id}/schema/{table} # 获取指定表的schema
│     Response: {table_name, ddl, columns}
│
├─ /training/
│  ├─ GET  /list                # 获取训练数据列表
│  │  Response: [{id, datasource_name, question, sql, source, is_approved}]
│  ├─ POST /add                 # 手动添加训练数据
│  │  Request: {datasource_id, question, sql}
│  ├─ PUT  /{id}                # 编辑训练数据
│  ├─ DELETE /{id}              # 删除训练数据
│  ├─ POST /auto-add            # 标记用户SQL为训练数据
│  │  Request: {query_history_id}
│  ├─ GET  /pending             # 获取待审核的自动训练数据
│  │  Response: [{id, question, sql, datasource_name, created_at}]
│  └─ POST /approve/{id}        # 审核通过自动训练数据
│     Response: {success, message}
│
└─ /settings/
   ├─ GET  /config              # 获取系统配置
   │  Response: {minimax_endpoint, minimax_model, timeout_seconds, max_rows}
   └─ PUT  /config              # 更新系统配置
      Request: {...}
```

### 4.2 数据模型

**DataSource（数据源配置）：**
```python
class DataSource:
    id: str                    # UUID
    name: str                  # 数据源名称
    type: str                  # clickhouse / postgresql / mysql
    host: str                  # 数据库地址
    port: int                  # 端口
    username: str              # 用户名
    password: str              # 密码（加密存储）
    database: str              # 数据库名
    is_active: bool            # 是否激活
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
```

**TrainingData（训练数据）：**
```python
class TrainingData:
    id: str                    # UUID
    datasource_id: str         # 关联数据源ID
    question: str              # 自然语言问题
    sql: str                   # SQL 查询语句
    source: str                # manual / auto
    is_approved: bool          # 是否审核通过
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
```

**QueryHistory（查询历史）：**
```python
class QueryHistory:
    id: str                    # UUID
    datasource_id: str         # 数据源ID
    question: str              # 用户问题
    generated_sql: str         # 生成的SQL
    final_sql: str             # 最终执行的SQL（用户可能修改）
    executed: bool             # 是否执行成功
    result_rows: int           # 返回行数
    execution_time: float      # 执行时间（秒）
    error_message: str         # 错误信息（如果有）
    created_at: datetime       # 创建时间
```

**SystemConfig（系统配置）：**
```python
class SystemConfig:
    minimax_endpoint: str      # MiniMax API endpoint
    minimax_model: str         # 模型名称
    minimax_api_key: str       # API密钥（加密存储）
    sql_timeout: int           # SQL执行超时（秒）
    max_result_rows: int       # 最大返回行数
    auto_train_enabled: bool   # 是否启用自动训练
```

---

## 五、Vanna Service 设计

### 5.1 核心功能模块

```python
class VannaService:
    """
    Vanna + ChromaDB + MiniMax-M2.7 集成服务
    提供 SQL 生成和训练数据管理
    """
    
    def __init__(self):
        """
        初始化 Vanna
        - 设置 MiniMax endpoint: 10.242.52.62:9924
        - 设置 model: MiniMax-M2.7
        - 配置 ChromaDB 持久化路径
        """
    
    def initialize_vanna():
        """
        初始化 Vanna，连接 MiniMax API
        使用 OpenAI 兼容接口配置
        """
    
    def train_sql(datasource_name: str, question: str, sql: str):
        """
        添加训练数据到 ChromaDB
        参数:
          - datasource_name: 数据源名称
          - question: 自然语言问题
          - sql: SQL 查询语句
        """
    
    def generate_sql(datasource_name: str, question: str) -> dict:
        """
        根据问题生成 SQL
        流程:
          1. 从 ChromaDB 检索相似训练数据
          2. 获取数据源的 DDL 信息
          3. 调用 MiniMax-M2.7 生成 SQL
        返回: {sql, confidence, related_training_data}
        """
    
    def add_ddl(datasource_name: str, ddl: str):
        """
        添加数据源的表结构信息
        参数:
          - datasource_name: 数据源名称
          - ddl: 表的 DDL 定义
        """
    
    def get_related_training_data(question: str, n: int = 5) -> list:
        """
        获取相似训练数据（用于前端展示）
        返回: [{question, sql, similarity}]
        """
    
    def extract_ddl_from_datasource(datasource_config: dict) -> list:
        """
        从数据源自动提取 DDL
        支持不同数据库类型:
          - ClickHouse: SHOW CREATE TABLE
          - PostgreSQL: pg_get_tabledef()
          - MySQL: SHOW CREATE TABLE
        返回: [{table_name, ddl}]
        """
```

### 5.2 数据源初始化流程

```
用户添加新数据源时：

Backend API 收到请求 →
1. 连接数据源，测试连接是否成功
   ↓
2. 提取表结构信息（DDL）
   - ClickHouse: SHOW CREATE TABLE
   - PostgreSQL: SELECT pg_get_tabledef()
   - MySQL: SHOW CREATE TABLE
   ↓
3. 调用 vanna_service.add_ddl() 存储到 ChromaDB
   ↓
4. 数据源配置存入 PostgreSQL
   ↓
5. 返回成功响应给前端
```

### 5.3 SQL 生成流程

```
用户提问 → Backend API → Vanna Service

1. 接收参数：datasource_name, question
   ↓
2. 从 ChromaDB 检索相关 DDL
   - 根据 datasource_name 查询
   ↓
3. 从 ChromaDB 检索相似训练数据
   - 使用向量相似度搜索
   - 返回 top-5 相关示例
   ↓
4. 构造 prompt:
   - DDL 信息（表结构）
   - 相似训练示例
   - 用户问题
   ↓
5. 调用 MiniMax-M2.7 API 生成 SQL
   - endpoint: 10.242.52.62:9924
   - model: MiniMax-M2.7
   - OpenAI 兼容接口
   ↓
6. 返回 SQL 给 Backend API
   ↓
7. Backend API 返回给前端展示
```

### 5.4 ChromaDB 管理

**数据存储结构：**
```
ChromaDB Collections:
├─ ddl_collection
│  └─ 存储数据源的 DDL 信息
│     Document: {datasource_name, table_name, ddl}
│
└─ training_collection
│  └─ 存储训练数据（问题-SQL对）
│     Document: {datasource_name, question, sql}
│
└─ documentation_collection (可选)
   └─ 存储业务文档，辅助 SQL 生成
```

**持久化配置：**
- ChromaDB 数据存储在 `/data/chromadb/` 目录
- Docker volume 映射：`chromadb-data:/data/chromadb`
- 容器重启后数据不丢失
- 提供备份脚本：`scripts/backup_chromadb.py`

---

## 六、Docker Compose 配置

### 6.1 服务定义

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

### 6.2 环境变量配置

**`.env` 文件：**
```bash
# MiniMax API 配置
MINIMAX_API_KEY=your_api_key_here

# 数据库密码（可选覆盖）
POSTGRES_PASSWORD=text2sql123

# 其他配置（可选）
SQL_TIMEOUT=60
MAX_RESULT_ROWS=1000
```

### 6.3 项目目录结构

```
Text2Sql/
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── components/
│   │   │   ├── AskInterface/
│   │   │   ├── DataSourceManager/
│   │   │   ├── TrainingManager/
│   │   │   └─ Settings/
│   │   ├── pages/
│   │   ├── services/
│   │   │   └─ api.ts
│   │   ├── App.tsx
│   │   └─ index.tsx
│   └── public/
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/
│   │   │   ├── ask.py
│   │   │   ├── datasources.py
│   │   │   ├── training.py
│   │   │   └ settings.py
│   │   ├── models/
│   │   │   ├── datasource.py
│   │   │   ├── training.py
│   │   │   └ history.py
│   │   ├── services/
│   │   │   ├── db_connector.py
│   │   │   ├── datasource_manager.py
│   │   │   └ training_manager.py
│   │   └ database.py
│   └ logs/
│
├── vanna-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── vanna_integration.py
│   │   ├── chromadb_manager.py
│   │   ├── ddl_extractor.py
│   │   └ config.py
│   ├── scripts/
│   │   ├── backup_chromadb.py
│   │   └ restore_chromadb.py
│   └ data/
│   │   └ chromadb/
│
├── docker-compose.yml
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

## 七、错误处理和容错设计

### 7.1 关键错误处理场景

**1. SQL 生成失败**
```
MiniMax API 调用失败:
├─ 重试机制（最多 3 次）
├─ 降级方案：返回提示用户重新提问
└─ 记录错误日志

ChromaDB 无相关训练数据:
├─ 提示用户先添加该数据源的表结构
└─ 建议：手动添加训练数据示例

生成的 SQL 有语法错误:
├─ Backend 捕获异常
├─ 返回错误信息给前端
└─ 用户可在前端手动修改 SQL
```

**2. 数据源连接失败**
```
添加数据源时连接测试失败:
├─ 返回具体错误类型
│  ├─ 认证失败（用户名/密码错误）
│  ├─ 网络不通（host/port 错误）
│  ├─ 数据库不存在
└─ 提示用户检查配置

执行 SQL 时连接断开:
├─ 返回连接错误
├─ 提示用户检查数据源状态
└─ 建议：重新测试连接
```

**3. SQL 执行错误**
```
SQL 权限不足:
├─ 返回权限错误
└─ 提示用户联系管理员

查询超时（大表查询）:
├─ 设置超时限制（默认 60 秒）
├─ 返回超时提示
└─ 建议用户优化查询（添加 WHERE/LIMIT）

结果集过大:
├─ 限制返回行数（默认 1000 行）
└─ 提示用户添加 LIMIT 条件
```

**4. 容器服务异常**
```
Vanna Service 宕机:
├─ Backend 返回服务不可用提示
├─ Docker 自动重启（restart: always）
└─ 健康检查机制

ChromaDB 数据损坏:
├─ 定期备份机制
└─ 提供恢复脚本

PostgreSQL 元数据丢失:
├─ Volume 持久化
└─ 定期备份（pg_dump）
```

### 7.2 日志记录策略

```
每个服务独立日志：

frontend:
├─ nginx logs（访问日志）
└─ 浏览器 console logs

backend-api:
├─ FastAPI logs
│  ├─ 请求日志（每个 API 调用）
│  ├─ 错误日志（异常堆栈）
│  └─ 业务日志（数据源操作）
└─ 存储路径: /app/logs

vanna-service:
├─ Vanna logs
│  ├─ SQL 生成日志
│  ├─ MiniMax API 调用日志
│  ├─ ChromaDB 操作日志
│  └─ DDL 提取日志
└─ 存储路径: /app/logs

postgres:
├─ PostgreSQL logs
└─ Docker logs 默认存储
```

---

## 八、测试策略

### 8.1 测试层级

**单元测试：**
```
Backend API 单元测试:
├─ pytest + pytest-asyncio
├─ 测试内容:
│  ├─ 数据源连接测试函数
│  ├─ SQL 执行函数
│  ├─ API 端点测试（模拟请求）
│  └─ 数据模型验证
└─ 运行: docker-compose exec backend-api pytest

Vanna Service 单元测试:
├─ pytest
├─ 测试内容:
│  ├─ SQL 生成函数（模拟 MiniMax API）
│  ├─ ChromaDB 训练数据函数
│  ├─ DDL 提取函数
│  └─ 向量检索函数
└─ 运行: docker-compose exec vanna-service pytest
```

**集成测试：**
```
API 集成测试:
├─ 测试完整的 SQL 生成流程
├─ 测试训练数据添加流程
├─ 使用测试数据库（避免污染真实数据）
└─ 测试容器间网络通信

数据源集成测试:
├─ ClickHouse/PostgreSQL/MySQL 连接测试
├─ DDL 提取测试
├─ SQL 执行测试
└─ 需要测试数据库环境（sample db）

Docker Compose 集成测试:
├─ 测试容器启动
├─ 测试服务间通信
└─ 测试数据持久化
```

**前端测试（可选）：**
```
Jest + React Testing Library:
├─ 测试关键 UI 组件
├─ 测试 API 调用逻辑
└─ 测试用户交互流程
```

**手动验收测试：**
```
验收流程:
├─ 一键启动流程测试
├─ 添加数据源 → 生成 SQL → 执行完整流程
├─ 训练数据管理流程测试
├─ 数据源切换测试
└─ 错误场景测试（连接失败、SQL 错误）
```

### 8.2 测试数据准备

```
测试用数据库环境:
├─ ClickHouse: sample_clickhouse_db（测试数据）
├─ PostgreSQL: sample_postgres_db（测试数据）
└─ MySQL: sample_mysql_db（测试数据）

预设训练数据:
├─ 常见查询示例（10-20 个）
├─ 用于验证 SQL 生成准确性
└─ 初始化脚本: scripts/init_training_data.py
```

---

## 九、部署和使用流程

### 9.1 部署流程

```bash
# 1. 克隆项目
git clone <repo-url>
cd Text2Sql

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 MINIMAX_API_KEY

# 3. 一键启动所有服务
docker-compose up -d

# 4. 检查服务状态
docker-compose ps
# 应该看到 4 个服务都是 Up 状态：
# - text2sql-frontend
# - text2sql-backend
# - text2sql-vanna
# - text2sql-postgres

# 5. 查看日志（可选）
docker-compose logs -f backend-api

# 6. 初始化训练数据（可选）
curl -X POST http://localhost:8000/api/v1/training/init

# 7. 访问前端界面
浏览器打开: http://localhost:3000
```

### 9.2 首次使用流程

```
步骤 1: 添加数据源
├─ 进入"数据源管理"页面
├─ 点击"添加数据源"
├─ 选择数据源类型（如 ClickHouse）
├─ 填写连接信息:
│  ├─ Name: 生产数据CK
│  ├─ Host: 10.x.x.x
│  ├─ Port: 9000
│  ├─ Username: default
│  ├─ Password: xxx
│  └─ Database: analytics_db
├─ 点击"测试连接"
├─ 连接成功后，点击"保存"
└─ 系统自动提取表结构（DDL）

步骤 2: 问数
├─ 进入"问数界面"
├─ 选择数据源"生产数据CK"
├─ 输入问题："查询昨天销售额前10的产品"
├─ 点击"生成SQL"
├─ 查看生成的 SQL
├─ 确认或修改 SQL
├─ 点击"执行"
└─ 查看结果表格

步骤 3: 添加训练数据（可选）
├─ 执行成功后，点击"添加为训练数据"
└─ 或在"训练数据管理"页面手动添加
```

### 9.3 运维操作

```bash
# 停止服务
docker-compose down

# 重启单个服务
docker-compose restart backend-api

# 备份 ChromaDB 数据
docker-compose exec vanna-service python scripts/backup_chromadb.py

# 备份 PostgreSQL 元数据
docker-compose exec postgres pg_dump -U text2sql text2sql > backup.sql

# 恢复 PostgreSQL 数据
cat backup.sql | docker-compose exec -T postgres psql -U text2sql text2sql

# 更新服务
git pull  # 拉取最新代码
docker-compose build  # 重新构建镜像
docker-compose up -d  # 重新启动

# 查看资源使用
docker stats text2sql-frontend text2sql-backend text2sql-vanna text2sql-postgres

# 清理日志
docker-compose exec backend-api rm -rf /app/logs/*.log
```

### 9.4 故障排查

```
问题 1: 前端无法访问
排查:
├─ docker-compose ps（检查 frontend 是否启动）
├─ docker logs text2sql-frontend（查看日志）
├─ 检查端口 3000 是否被占用
└─ 浏览器访问 http://localhost:3000

问题 2: SQL 生成失败
排查:
├─ docker logs text2sql-vanna（查看 Vanna 日志）
├─ 检查 MINIMAX_API_KEY 是否正确
├─ 检查 MiniMax endpoint 是否可访问:
│  curl http://10.242.52.62:9924/v1/models
├─ 检查 ChromaDB 是否有训练数据
└─ 检查数据源 DDL 是否已提取

问题 3: 数据源连接失败
排查:
├─ 使用"测试连接"功能
├─ 检查网络连通性:
│  ping <datasource_host>
│  telnet <datasource_host> <port>
├─ 检查用户名密码是否正确
├─ 检查数据库是否存在
└─ 检查防火墙规则

问题 4: ChromaDB 数据丢失
排查:
├─ docker volume ls（检查 volume 是否存在）
├─ 检查 docker-compose.yml volume 配置
├─ 使用备份恢复脚本:
│  docker-compose exec vanna-service python scripts/restore_chromadb.py
└─ 重新添加数据源和训练数据

问题 5: PostgreSQL 元数据丢失
排查:
├─ docker volume ls（检查 postgres-data volume）
├─ 使用备份恢复:
│  cat backup.sql | docker-compose exec -T postgres psql -U text2sql text2sql
└─ 重新初始化数据库
```

---

## 十、关键约束和注意事项

### 10.1 技术约束

1. **MiniMax API 限制**
   - 必须确保 endpoint `10.242.52.62:9924` 可访问
   - API Key 需要妥善保管，不要泄露
   - OpenAI 兼容接口，确保调用格式正确

2. **数据源网络限制**
   - 数据源在其他服务器，需要确保网络连通
   - 可能需要配置防火墙规则
   - 确保数据库用户权限足够（读取表结构）

3. **ChromaDB 性能**
   - ChromaDB 是轻量级向量库，适合中小规模训练数据
   - 如果训练数据量超过 10 万条，建议考虑其他向量库（如 Milvus）

4. **容器资源限制**
   - 默认配置适合小团队使用（<10 人）
   - 如果用户量大，建议增加容器资源限制（CPU、内存）

### 10.2 安全注意事项

1. **数据源密码加密**
   - PostgreSQL 中存储的数据源密码需要加密
   - 使用 AES 或类似加密算法
   - 加密密钥存储在环境变量中

2. **MiniMax API Key 保护**
   - API Key 存储在 `.env` 文件中
   - `.env` 文件不要提交到 Git（已在 .gitignore）
   - 使用环境变量传递给容器

3. **内部网络安全**
   - 所有服务在 docker network 内通信
   - Backend API 只暴露必要端口（8000）
   - Vanna Service 和 PostgreSQL 不对外暴露端口（可选）

4. **无认证风险**
   - 当前设计无用户认证，仅适合内网环境
   - 如果需要对外访问，必须添加认证机制

### 10.3 性能优化建议

1. **SQL 执行优化**
   - 设置查询超时（默认 60 秒）
   - 限制结果行数（默认 1000 行）
   - 大表查询建议添加索引

2. **训练数据优化**
   - 定期清理低质量训练数据
   - 添加多样化的训练示例
   - 针对每个数据源添加专属训练数据

3. **MiniMax API 调用优化**
   - 缓存相似问题的 SQL 结果
   - 批量训练数据添加时，考虑并发控制
   - 监控 API 调用频率和成本

---

## 十一、未来扩展方向

### 11.1 功能扩展

1. **用户认证和权限控制**
   - 添加用户登录机制
   - 数据源权限分级（不同用户访问不同数据源）
   - 查询历史追踪和审计

2. **查询结果可视化**
   - 支持多种图表类型（折线图、柱状图、饼图）
   - 自动识别数据类型，推荐合适的图表
   - 导出图表功能

3. **协作功能**
   - 查询分享（分享 SQL 和结果给其他用户）
   - 训练数据协作（团队成员共同维护训练数据）
   - 查询模板库（保存常用查询为模板）

4. **高级训练数据管理**
   - 自动质量评估（评估训练数据的效果）
   - 冗余数据检测（避免重复或矛盾的训练数据）
   - 训练数据版本管理

### 11.2 技术升级

1. **向量库升级**
   - 如果训练数据量大，升级到 Milvus 或 Qdrant
   - 支持更高效的向量检索

2. **LLM 升级**
   - 支持多个 LLM 提供商（OpenAI、国产大模型切换）
   - 模型效果对比和选择

3. **高可用部署**
   - 添加负载均衡（多个 Backend API 容器）
   - PostgreSQL 主从复制
   - ChromaDB 集群部署

4. **监控和告警**
   - 添加 Prometheus 监控
   - Grafana 可视化仪表盘
   - 关键指标告警（API 错误率、容器资源使用）

---

## 十二、成功标准

### 12.1 功能验收标准

✅ **核心功能：**
- 用户可以通过自然语言生成 SQL
- 生成的 SQL 可以正确执行并返回结果
- 用户可以添加、编辑、删除数据源
- 用户可以管理训练数据（手动添加 + 自动训练）
- 所有服务通过 docker-compose 一键启动

✅ **性能标准：**
- SQL 生成时间 < 5 秒（90% 的情况）
- SQL 执行超时限制 60 秒
- 支持 ClickHouse、PostgreSQL、MySQL 三种数据源

✅ **稳定性标准：**
- Docker 容器重启后数据不丢失
- 单个服务故障不影响其他服务
- 提供数据备份和恢复机制

### 12.2 项目交付物

✅ **代码交付：**
- 完整的前端代码（React + TypeScript）
- 完整的后端代码（FastAPI）
- 完整的 Vanna Service 代码
- Docker Compose 配置文件
- Dockerfile（每个服务）

✅ **文档交付：**
- README.md（项目说明和快速开始）
- 设计文档（本文档）
- API 文档（FastAPI 自动生成）
- 部署文档（详细部署步骤）
- 故障排查文档

✅ **测试交付：**
- 单元测试代码和测试报告
- 集成测试流程
- 手动验收测试报告

✅ **运维交付：**
- 数据备份脚本
- 数据恢复脚本
- 监控脚本（可选）
- 日志管理脚本

---

## 附录

### A. API 详细文档

（FastAPI 启动后自动生成，访问 http://localhost:8000/docs）

### B. 数据库 Schema 详细定义

（见 backend/app/models/ 目录）

### C. 环境变量完整列表

```bash
# MiniMax API 配置
MINIMAX_API_KEY=<required>
MINIMAX_ENDPOINT=http://10.242.52.62:9924
MINIMAX_MODEL=MiniMax-M2.7

# PostgreSQL 配置
DATABASE_URL=postgresql://text2sql:text2sql123@postgres:5432/text2sql
POSTGRES_USER=text2sql
POSTGRES_PASSWORD=text2sql123
POSTGRES_DB=text2sql

# Backend API 配置
VANNA_SERVICE_URL=http://vanna-service:8001
CORS_ORIGINS=http://localhost:3000
SQL_TIMEOUT=60
MAX_RESULT_ROWS=1000

# ChromaDB 配置
CHROMADB_PATH=/data/chromadb
```

### D. 常用命令速查

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f <service-name>

# 重启服务
docker-compose restart <service-name>

# 进入容器
docker-compose exec <service-name> bash

# 查看容器状态
docker-compose ps

# 重新构建镜像
docker-compose build

# 备份数据
docker-compose exec postgres pg_dump text2sql > backup.sql
docker-compose exec vanna-service python scripts/backup_chromadb.py
```

---

**文档状态：** 完成  
**下一步：** 实现计划编写（使用 writing-plans skill）
