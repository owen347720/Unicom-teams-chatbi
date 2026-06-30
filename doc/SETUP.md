# 部署和使用流程

## 部署流程

### 前置要求

- Docker 和 Docker Compose 已安装
- MiniMax API Key 已获取
- 网络可访问 MiniMax endpoint: 10.242.52.62:9924
- 网络可访问目标数据源服务器

### 部署步骤

#### 1. 克隆项目

```bash
git clone <repo-url>
cd Text2Sql
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
vim .env
```

**.env 文件内容：**
```bash
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
```

#### 3. 一键启动所有服务

```bash
# 启动所有容器
docker-compose up -d

# 查看容器状态
docker-compose ps

# 应该看到 4 个服务都是 Up 状态：
# NAME                STATUS    PORTS
# text2sql-frontend   Up        0.0.0.0:3000->3000/tcp
# text2sql-backend    Up        0.0.0.0:8000->8000/tcp
# text2sql-vanna      Up        0.0.0.0:8001->8001/tcp
# text2sql-postgres   Up        0.0.0.0:5432->5432/tcp
```

#### 4. 验证服务健康

```bash
# 检查 Backend API 健康状态
curl http://localhost:8000/health

# 应返回：
# {"status": "healthy", "services": {...}}

# 检查 Vanna Service 健康状态
curl http://localhost:8001/health

# 应返回：
# {"status": "healthy"}
```

#### 5. 初始化训练数据（可选）

```bash
# 导入预设训练数据示例
curl -X POST http://localhost:8000/api/v1/training/init

# 应返回：
# {"message": "Training data initialized", "total_added": 20}
```

#### 6. 访问前端界面

浏览器打开：http://localhost:3000

---

## 首次使用流程

### 步骤 1：添加数据源

1. 进入"数据源管理"页面
2. 点击"添加数据源"按钮
3. 选择数据源类型（ClickHouse / PostgreSQL / MySQL）
4. 填写连接配置：

**ClickHouse 示例：**
```
Name: 生产数据CK
Host: 10.1.2.3
Port: 9000
Username: default
Password: your_password
Database: analytics_db
```

**PostgreSQL 示例：**
```
Name: 订单数据库PG
Host: 10.1.2.4
Port: 5432
Username: postgres
Password: your_password
Database: orders_db
```

**MySQL 示例：**
```
Name: 用户数据库MySQL
Host: 10.1.2.5
Port: 3306
Username: root
Password: your_password
Database: users_db
```

5. 点击"测试连接"
   - 成功：显示"连接成功，发现 25 个表"
   - 失败：显示具体错误信息
6. 连接成功后，点击"保存"
7. 系统自动提取表结构（DDL）并存储到 ChromaDB

---

### 步骤 2：问数

1. 进入"问数界面"
2. 选择数据源（如"生产数据CK"）
3. 在输入框输入自然语言问题：
   - "查询昨天销售额前10的产品"
   - "统计上周每天的订单数量"
   - "找出购买次数最多的用户"
4. 点击"生成 SQL"
5. 系统显示生成的 SQL（可在 Monaco Editor 中修改）
6. 点击"执行"
7. 查看结果表格
8. 可选择"添加为训练数据"（提升下次生成准确性）

---

### 步骤 3：管理训练数据

**手动添加训练数据：**

1. 进入"训练数据管理"页面
2. 点击"添加训练数据"
3. 选择数据源
4. 输入问题和 SQL 示例：
   ```
   问题: 查询昨天的订单数量
   SQL: SELECT COUNT(*) FROM orders WHERE date = yesterday()
   ```
5. 点击"保存"

**审核自动训练数据：**

1. 进入"待审核训练数据"列表
2. 查看用户执行后标记的 SQL
3. 点击"审核通过"或"删除"

---

## 运维操作

### 日常运维

#### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend-api
docker-compose logs -f vanna-service

# 查看最近 100 行日志
docker-compose logs --tail=100 backend-api
```

#### 重启服务

```bash
# 重启单个服务
docker-compose restart backend-api
docker-compose restart vanna-service

# 重启所有服务
docker-compose restart
```

#### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除 volumes（清空数据）
docker-compose down -v
```

---

### 数据备份

#### 备份 PostgreSQL 元数据

```bash
# 导出数据库
docker-compose exec postgres pg_dump -U text2sql text2sql > backup_$(date +%Y%m%d).sql

# 恢复数据库
cat backup_20260630.sql | docker-compose exec -T postgres psql -U text2sql text2sql
```

#### 备份 ChromaDB 向量数据

```bash
# 执行备份脚本
docker-compose exec vanna-service python scripts/backup_chromadb.py

# 备份文件位置：
# /data/backups/chromadb_backup_YYYYMMDD_HHMMSS.json

# 恢复 ChromaDB
docker-compose exec vanna-service python scripts/restore_chromadb.py /data/backups/chromadb_backup_xxx.json
```

---

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build

# 重新启动服务
docker-compose up -d

# 或者一步完成：
docker-compose up -d --build
```

---

### 监控资源使用

```bash
# 查看容器资源使用
docker stats text2sql-frontend text2sql-backend text2sql-vanna text2sql-postgres

# 查看容器详细信息
docker-compose exec backend-api ps aux
```

---

## 故障排查

### 问题 1：前端无法访问

**现象：** 浏览器无法打开 http://localhost:3000

**排查步骤：**

```bash
# 1. 检查 frontend 容器状态
docker-compose ps frontend

# 2. 查看前端日志
docker-compose logs frontend

# 3. 检查端口占用
lsof -i :3000

# 4. 检查 nginx 配置
docker-compose exec frontend nginx -t
```

**解决方案：**
- 如果容器未启动：`docker-compose restart frontend`
- 如果端口被占用：修改 docker-compose.yml 端口配置
- 如果 nginx 配置错误：检查 `frontend/nginx.conf`

---

### 问题 2：SQL 生成失败

**现象：** 点击"生成 SQL"返回错误

**排查步骤：**

```bash
# 1. 查看 Backend API 日志
docker-compose logs backend-api | grep error

# 2. 查看 Vanna Service 日志
docker-compose logs vanna-service | grep error

# 3. 检查 MiniMax endpoint 可达性
curl http://10.242.52.62:9924/v1/models

# 4. 检查 API Key 是否正确
docker-compose exec backend-api printenv | grep MINIMAX

# 5. 检查 ChromaDB 训练数据
curl http://localhost:8001/training/count
```

**解决方案：**
- MiniMax endpoint 不可达：检查网络连接
- API Key 错误：更新 .env 文件中的 MINIMAX_API_KEY
- ChromaDB 无训练数据：先添加数据源和训练数据
- Vanna Service 宕机：`docker-compose restart vanna-service`

---

### 问题 3：数据源连接失败

**现象：** 添加数据源时"测试连接"失败

**排查步骤：**

```bash
# 1. 检查网络连通性
ping <datasource_host>

# 2. 检查端口可达性
telnet <datasource_host> <port>

# 3. 查看 Backend API 日志
docker-compose logs backend-api | grep connection

# 4. 手动测试数据库连接
docker-compose exec backend-api python scripts/test_db_connection.py
```

**解决方案：**
- 网络不通：检查防火墙规则、VPN 连接
- 认证失败：检查用户名密码、数据库权限
- 数据库不存在：确认数据库名称正确
- 端口错误：确认端口号（ClickHouse 9000、PostgreSQL 5432、MySQL 3306）

---

### 问题 4：SQL 执行超时

**现象：** SQL 执行时间过长或超时

**排查步骤：**

```bash
# 1. 查看执行日志
docker-compose logs backend-api | grep timeout

# 2. 检查数据源响应时间
curl -X POST http://localhost:8000/api/v1/datasources/{id}/test

# 3. 检查超时配置
curl http://localhost:8000/api/v1/settings/config | grep timeout
```

**解决方案：**
- 增加 SQL 超时时间：更新系统配置 `sql_timeout`
- 优化 SQL：添加 WHERE 条件、LIMIT 限制
- 添加索引：在目标数据源上创建合适的索引
- 减少结果行数：添加 LIMIT 子句

---

### 问题 5：ChromaDB 数据丢失

**现象：** 训练数据或 DDL 信息丢失

**排查步骤：**

```bash
# 1. 检查 volume 是否存在
docker volume ls | grep chromadb

# 2. 检查 ChromaDB 路径
docker-compose exec vanna-service ls -la /data/chromadb

# 3. 检查 ChromaDB 数据量
curl http://localhost:8001/training/count
```

**解决方案：**
- Volume 未创建：`docker-compose down -v && docker-compose up -d`（重新创建）
- 使用备份恢复：`python scripts/restore_chromadb.py backup_file.json`
- 重新添加数据源：会自动提取 DDL
- 重新添加训练数据：手动添加或标记历史查询

---

### 问题 6：容器启动失败

**现象：** docker-compose up 后部分容器未启动

**排查步骤：**

```bash
# 1. 查看容器状态
docker-compose ps

# 2. 查看启动日志
docker-compose logs

# 3. 检查 Dockerfile
cat backend/Dockerfile

# 4. 检查依赖服务
docker-compose config
```

**解决方案：**
- 依赖服务未就绪：增加 `depends_on` 配置
- Dockerfile 错误：检查构建脚本
- 端口冲突：修改端口配置
- 资源不足：增加 Docker 资源限制

---

## 高级配置

### 自定义端口配置

修改 `docker-compose.yml`：

```yaml
services:
  frontend:
    ports:
      - "8080:3000"  # 使用 8080 端口
  
  backend-api:
    ports:
      - "8888:8000"  # 使用 8888 端口
```

### 资源限制配置

```yaml
services:
  backend-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 日志持久化

```yaml
services:
  backend-api:
    volumes:
      - ./logs:/app/logs
```

---

## 性能优化建议

### 1. SQL 执行优化

- 设置合理的超时时间（60-120 秒）
- 限制结果行数（1000-5000 行）
- 在数据源上创建必要的索引
- 避免全表扫描，添加 WHERE 条件

### 2. 训练数据优化

- 定期清理低质量训练数据
- 添加多样化的示例（覆盖不同查询场景）
- 针对不同数据源添加专属训练数据
- 审核"自动添加"的训练数据，保证质量

### 3. ChromaDB 优化

- 定期备份 ChromaDB 数据
- 监控向量库大小（建议 <10 万条记录）
- 如果数据量大，考虑升级到 Milvus

### 4. MiniMax API 优化

- 监控 API 调用频率和成本
- 缓存相似问题的 SQL 结果
- 批量添加训练数据时控制并发

---

## 常用命令速查表

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f <service>

# 重启服务
docker-compose restart <service>

# 进入容器
docker-compose exec <service> bash

# 备份数据库
docker-compose exec postgres pg_dump text2sql > backup.sql

# 备份 ChromaDB
docker-compose exec vanna-service python scripts/backup_chromadb.py

# 更新服务
git pull && docker-compose up -d --build

# 清理日志
docker-compose exec backend-api rm -rf /app/logs/*.log

# 查看资源
docker stats
```

---

## 更新日期

2026-06-30