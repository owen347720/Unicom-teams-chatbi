diff --git a/.env.example b/.env.example
new file mode 100644
index 0000000..ca1ab51
--- /dev/null
+++ b/.env.example
@@ -0,0 +1,13 @@
+# MiniMax API 配置（必需）
+MINIMAX_API_KEY=your_api_key_here
+
+# PostgreSQL 配置（可选，有默认值）
+POSTGRES_USER=text2sql
+POSTGRES_PASSWORD=text2sql123
+POSTGRES_DB=text2sql
+
+# 系统配置（可选）
+SQL_TIMEOUT=60
+MAX_RESULT_ROWS=1000
+AUTO_TRAIN_ENABLED=true
+LOG_LEVEL=INFO
diff --git a/.gitignore b/.gitignore
new file mode 100644
index 0000000..109614d
--- /dev/null
+++ b/.gitignore
@@ -0,0 +1,33 @@
+# Environment variables
+.env
+.env.local
+*.key
+
+# Logs
+*.log
+logs/
+
+# Dependencies
+node_modules/
+__pycache__/
+*.pyc
+.pyo
+
+# Build artifacts
+dist/
+build/
+*.egg-info/
+
+# IDE
+.vscode/
+.idea/
+*.swp
+*.swo
+
+# OS
+.DS_Store
+Thumbs.db
+
+# Docker volumes (local)
+chromadb-data/
+postgres-data/
diff --git a/README.md b/README.md
new file mode 100644
index 0000000..630fba7
--- /dev/null
+++ b/README.md
@@ -0,0 +1,25 @@
+# Text2Sql - 团队内取数系统
+
+基于 Vanna 的 Text2SQL 问数系统，支持自然语言转 SQL 查询。
+
+## 快速开始
+
+```bash
+# 1. 配置环境变量
+cp .env.example .env
+# 编辑 .env 文件，填入 MINIMAX_API_KEY
+
+# 2. 一键启动
+docker-compose up -d
+
+# 3. 访问界面
+浏览器打开: http://localhost:3000
+```
+
+## 详细文档
+
+见 `doc/` 目录。
+
+## 更新日期
+
+2026-06-30
