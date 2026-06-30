# Task 5: 实现 FastAPI 服务端点

## 任务描述

实现 Vanna Service 的 FastAPI REST API 端点，对外提供服务接口。

## 文件清单

需要创建的文件：
- `vanna-service/app/main.py`
- `vanna-service/tests/test_main.py`

## 接口定义

此任务产生：REST API 端点
- `/health` - 健康检查
- `/train/ddl` - 训练 DDL 信息
- `/train/sql` - 训练问题-SQL对
- `/generate` - 生成 SQL
- `/similar/{question}` - 获取相似训练数据

此任务消费：`VannaService` 类（Task 4 实现）

## Global Constraints

- FastAPI 应用：title="Vanna Service", version="1.0.0"
- 端口：8001（已在 Dockerfile 配置）
- 日志：使用 loguru，保存到 `/app/logs/vanna.log`
- Request models 使用 Pydantic BaseModel

## TDD 流程

### Step 1: 编写测试（失败）

创建 test_main.py，包含：
- test_health_check
- test_train_ddl_endpoint
- test_train_sql_endpoint
- test_generate_endpoint

### Step 2: 运行测试（失败）

```bash
cd vanna-service
pytest tests/test_main.py -v
```

Expected: FAIL - ModuleNotFoundError

### Step 3: 实现 FastAPI 应用

创建 main.py，包含：
- FastAPI 应用初始化
- startup_event 初始化 VannaService
- 4 个 Request models
- 5 个 API endpoints
- loguru 日志配置

### Step 4: 运行测试（通过）

```bash
cd vanna-service
pytest tests/test_main.py -v
```

Expected: PASS

### Step 5: Commit

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

## 报告要求

完成后，请在 `/Users/owen/coding/2026-自学/Text2Sql/.superpowers/sdd/task-5-report.md` 编写报告，包含：
1. TDD 流程执行情况
2. 测试运行结果
3. Commit hash
4. 任何问题或关注点
5. 返回状态（DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED）