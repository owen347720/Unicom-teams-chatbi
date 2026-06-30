# 架构设计

## 整体架构

采用微服务架构，三个主要服务容器：

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

## 服务职责

### Frontend（前端容器）

**职责：**
- 提供用户交互界面
- 问数主界面（问题输入、SQL预览、结果展示）
- 数据源管理页面（添加/编辑/删除数据源）
- 训练数据管理页面（管理训练示例）

**技术栈：**
- React 18 + TypeScript
- Ant Design 5.x（ProComponents）
- Axios（API 请求）
- React Query（状态管理）
- Monaco Editor（SQL 编辑器）

**端口：** 3000

### Backend API（后端容器）

**职责：**
- 处理前端 API 请求
- 数据源连接管理
- SQL 执行和结果处理
- 元数据存储（PostgreSQL）
- 调用 Vanna Service 生成 SQL

**技术栈：**
- FastAPI（Python Web 框架）
- PostgreSQL（元数据存储）
- SQLAlchemy（ORM）

**端口：** 8000

### Vanna Service（AI 服务容器）

**职责：**
- SQL 生成（基于 Vanna + MiniMax-M2.7）
- 训练数据管理（ChromaDB）
- DDL 提取和存储
- 向量检索

**技术栈：**
- Vanna（Text2SQL 框架）
- ChromaDB（向量数据库）
- MiniMax-M2.7（LLM，endpoint: 10.242.52.62:9924）

**端口：** 8001（内部通信）

### PostgreSQL（元数据容器）

**职责：**
- 存储数据源配置
- 存储训练数据元信息
- 存储查询历史记录
- 存储系统配置

**技术栈：**
- PostgreSQL 15

**端口：** 5432（内部）

## 数据流

### SQL 生成流程

```
用户输入问题
↓
Frontend 发送请求到 Backend API
↓
Backend API 调用 Vanna Service
↓
Vanna Service:
  1. 从 ChromaDB 检索相关 DDL
  2. 从 ChromaDB 检索相似训练数据
  3. 构造 prompt（DDL + 示例 + 问题）
  4. 调用 MiniMax-M2.7 API 生成 SQL
↓
返回 SQL 到 Backend API
↓
返回 SQL 到 Frontend 展示
↓
用户确认/修改 SQL
↓
Frontend 发送执行请求到 Backend API
↓
Backend API 连接数据源执行 SQL
↓
返回结果到 Frontend 展示
```

### 数据源添加流程

```
用户填写数据源配置
↓
Frontend 发送到 Backend API
↓
Backend API 测试连接
↓
连接成功后，提取表结构（DDL）
↓
Backend API 调用 Vanna Service 存储 DDL
↓
Vanna Service 将 DDL 存入 ChromaDB
↓
Backend API 将数据源配置存入 PostgreSQL
↓
返回成功响应到 Frontend
```

## 容器编排

使用 Docker Compose 编排所有服务：

```yaml
services:
  frontend:
    - React 容器
    - 端口 3000
    - 依赖 backend-api
    
  backend-api:
    - FastAPI 容器
    - 端口 8000
    - 依赖 vanna-service, postgres
    
  vanna-service:
    - Vanna + ChromaDB 容器
    - 端口 8001
    - Volume: chromadb-data
    
  postgres:
    - PostgreSQL 容器
    - 端口 5432
    - Volume: postgres-data
```

## 网络设计

- 所有服务在 `text2sql-network` 桥接网络中
- Frontend → Backend API: HTTP (端口 8000)
- Backend API → Vanna Service: HTTP (端口 8001)
- Backend API → PostgreSQL: PostgreSQL 协议 (端口 5432)
- Backend API → 外部数据源: SQL 协议（ClickHouse/PostgreSQL/MySQL）

## 数据持久化

**ChromaDB（向量数据）：**
- Volume: `chromadb-data`
- 存储路径: `/data/chromadb/`
- 内容：DDL 信息、训练数据向量

**PostgreSQL（元数据）：**
- Volume: `postgres-data`
- 存储内容：数据源配置、训练数据元信息、查询历史

**日志：**
- Backend logs: `./backend/logs`
- Vanna logs: `/app/logs`

## 技术选型理由

### 为什么选择 Vanna？

- 专为 Text2SQL 设计的框架
- 支持训练数据管理（RAG）
- 支持多种 LLM（包括 OpenAI 兼容接口）
- 支持多种数据库（ClickHouse/PostgreSQL/MySQL）
- 开源且文档完善

### 为什么选择 ChromaDB？

- Vanna 官方默认支持
- 轻量级，纯 Python 实现
- 容器化部署简单
- 适合中小规模训练数据（<10万条）
- 持久化存储支持

### 为什么选择 MiniMax-M2.7？

- 国产大模型，合规性好
- 提供 OpenAI 兼容接口，集成简单
- 内网部署 endpoint: 10.242.52.62:9924
- 数据不出内网，安全可控

### 为什么选择 React + Ant Design？

- 成熟的组件库（Ant Design Pro）
- TypeScript 支持好，适合团队协作
- Monaco Editor 提供 SQL 编辑功能
- 后台管理界面模板现成

### 为什么选择 FastAPI？

- 性能优秀，异步支持
- 自动生成 API 文档（Swagger）
- Python 生态，与 Vanna 集成方便
- 类型提示支持好

## 扩展性考虑

### 横向扩展

- Backend API 可以部署多个容器（负载均衡）
- Vanna Service 可以部署多个容器
- PostgreSQL 可以配置主从复制

### 功能扩展

- 添加用户认证（JWT）
- 添加权限控制（数据源级别）
- 添加查询结果可视化（图表）
- 升级向量库（Milvus/Qdrant）
- 支持更多数据源类型

## 设计文档

完整设计文档见：`docs/superpowers/specs/2026-06-30-vanna-text2sql-design.md`

## 更新日期

2026-06-30