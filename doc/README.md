# Text2Sql - 团队内取数系统

基于 Vanna 的 Text2SQL 问数系统，支持自然语言转 SQL 查询，一键 Docker 部署。

## 项目目标

构建一个团队内取数项目，实现自然语言问数功能，所有服务容器化部署，支持数据源插拔，特别支持 ClickHouse 数据库。

## 核心特性

- ✅ 自然语言转 SQL 查询（基于 Vanna + MiniMax-M2.7）
- ✅ 前后端分离架构（React + FastAPI）
- ✅ 完全容器化部署（docker-compose 一键启动）
- ✅ Web UI 管理数据源（支持新增/编辑/删除）
- ✅ 支持主流数据库（ClickHouse、PostgreSQL、MySQL）
- ✅ 训练数据管理（手动添加 + 自动训练）

## 技术栈

**前端：** React 18 + TypeScript + Ant Design 5.x  
**后端：** FastAPI + PostgreSQL  
**AI 服务：** Vanna + ChromaDB + MiniMax-M2.7  
**部署：** Docker + docker-compose

## 快速开始

```bash
# 1. 克隆项目
git clone <repo-url>
cd Text2Sql

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 MINIMAX_API_KEY

# 3. 一键启动所有服务
docker-compose up -d

# 4. 访问前端界面
浏览器打开: http://localhost:3000
```

## 服务端口

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- Vanna Service：http://localhost:8001（内部）
- PostgreSQL：localhost:5432（内部）

## 文档目录

- [架构设计](ARCHITECTURE.md) - 整体架构和技术选型
- [API 设计](API.md) - 后端 API 端点设计
- [Vanna 集成](VANNA_INTEGRATION.md) - Vanna 服务设计
- [部署流程](SETUP.md) - 详细部署和使用说明
- [A100 远程运维](A100_REMOTE_OPS.md) - A100BMS-2 部署目录、端口、健康检查和常用运维命令
- [评测基准](EVAL.md) - V1.2 schema-driven 1000 题 benchmark 和运行方式
- [持续优化](CONTINUOUS_OPTIMIZATION.md) - 基线指标、优化 backlog 和后续对比口径
- [安全注意事项](SECURITY.md) - 安全配置和风险提示

## 详细设计文档

完整的设计文档见：`docs/superpowers/specs/2026-06-30-vanna-text2sql-design.md`

## 当前状态

项目已完成容器化前后端与 A100BMS-2 服务器部署验证。当前主评测基准为
`benchmark/v1.2-schema-gold-1000`，gold SQL 已在 A100 执行验证通过。

## 更新日期

2026-07-03
