# Task 1: 创建项目目录结构

## 任务描述

创建项目的基础目录结构，包括前端、后端和 Vanna Service 的目录，以及必要的配置文件。

## 文件清单

需要创建的文件：
- `frontend/`, `backend/`, `vanna-service/` 目录结构
- `.gitignore`
- `.env.example`
- `README.md`

## 接口定义

此任务产生：项目基础目录结构，供后续任务使用

## Global Constraints

必须遵循以下全局约束：
- MiniMax endpoint: `10.242.52.62:9924`
- MiniMax model: `MiniMax-M2.7`
- SQL 执行超时: 60 秒
- 最大返回行数: 1000 行
- 数据源类型: ClickHouse / PostgreSQL / MySQL
- ChromaDB 持久化路径: `/data/chromadb`
- PostgreSQL 连接: `postgresql://text2sql:text2sql123@postgres:5432/text2sql`
- 无用户认证（内部工具）
- 数据源密码需要加密存储
- API Key 存储在 `.env` 文件，不提交到 Git

## 实现步骤

### Step 1: 创建目录结构

```bash
# 创建主要目录
mkdir -p frontend backend vanna-service

# 创建子目录
mkdir -p frontend/src/components frontend/src/pages frontend/src/services frontend/public
mkdir -p backend/app/routers backend/app/models backend/app/services backend/logs
mkdir -p vanna-service/app vanna-service/scripts vanna-service/data/chromadb
```

### Step 2: 创建 .gitignore

```bash
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

### Step 3: 创建 .env.example

```bash
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

### Step 4: 创建 README.md

```bash
cat > README.md << 'EOF'
# Text2Sql - 团队内取数系统

基于 Vanna 的 Text2SQL 问数系统，支持自然语言转 SQL 查询。

## 快速开始

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 MINIMAX_API_KEY

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

### Step 5: 验证目录结构

```bash
tree -L 3 -I 'node_modules|__pycache__|.git'
```

Expected: 显示完整目录结构

### Step 6: Commit

```bash
git add .gitignore .env.example README.md
git commit -m "chore: initialize project structure

- Add directory structure for frontend/backend/vanna-service
- Add .gitignore for environment files and logs
- Add .env.example template
- Add initial README.md"
```

## 上下文说明

这是项目的第一个任务，创建了基础的项目结构。后续任务将在此基础上构建：
- Task 2 会添加 docker-compose.yml
- Task 3-7 会实现 Vanna Service
- Task 8-15 会实现 Backend API
- Task 16-25 会实现 Frontend

## 报告要求

完成后，请在 `/Users/owen/coding/2026-自学/Text2Sql/.superpowers/sdd/task-1-report.md` 文件中编写报告，包含：
1. 执行的步骤
2. 测试结果（如果有）
3. Commit hash
4. 任何发现的问题或关注点
5. 返回状态（DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED）

报告格式示例：
```markdown
# Task 1 Report

## 执行步骤
- Step 1: ✓ 创建目录结构
- Step 2: ✓ 创建 .gitignore
- Step 3: ✓ 创建 .env.example
- Step 4: ✓ 创建 README.md
- Step 5: ✓ 验证目录结构
- Step 6: ✓ Commit

## 测试结果
无测试（这是基础设施任务）

## Commit
Commit: abc1234

## 问题/关注点
无

## 状态
DONE
```