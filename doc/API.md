# API 设计文档

## API 端点总览

Base URL: `http://localhost:8000/api/v1`

## 1. Ask API（问数接口）

### 1.1 生成 SQL

**POST** `/ask/generate-sql`

生成 SQL 查询语句，但不执行。

**Request:**
```json
{
  "datasource_id": "uuid-string",
  "question": "查询昨天销售额前10的产品"
}
```

**Response:**
```json
{
  "sql": "SELECT product_name, SUM(amount) as total_sales FROM orders WHERE date = yesterday() ORDER BY total_sales DESC LIMIT 10",
  "confidence": 0.85,
  "related_training_data": [
    {
      "question": "查询销售额最高的产品",
      "sql": "SELECT product_name, SUM(amount) FROM orders GROUP BY product_name ORDER BY SUM(amount) DESC LIMIT 10",
      "similarity": 0.92
    }
  ]
}
```

**错误响应:**
```json
{
  "error": "SQL generation failed",
  "message": "No training data found for this datasource",
  "suggestion": "Please add training data for this datasource first"
}
```

---

### 1.2 执行 SQL

**POST** `/ask/execute-sql`

执行 SQL 查询并返回结果。

**Request:**
```json
{
  "datasource_id": "uuid-string",
  "sql": "SELECT * FROM products LIMIT 10",
  "timeout": 60  // optional, default 60 seconds
}
```

**Response:**
```json
{
  "columns": ["id", "product_name", "price", "stock"],
  "rows": [
    [1, "iPhone 15", 5999, 100],
    [2, "MacBook Pro", 12999, 50],
    // ...
  ],
  "row_count": 10,
  "execution_time": 0.5,
  "truncated": false  // 是否因超过限制被截断
}
```

**错误响应:**
```json
{
  "error": "SQL execution failed",
  "message": "Query timeout after 60 seconds",
  "suggestion": "Please optimize your query or add LIMIT clause"
}
```

---

### 1.3 获取查询历史

**GET** `/ask/history`

获取用户的查询历史记录。

**Query Parameters:**
- `datasource_id` (optional): 过滤特定数据源
- `limit` (optional): 返回数量，默认 20
- `offset` (optional): 偏移量，默认 0

**Response:**
```json
{
  "total": 50,
  "items": [
    {
      "id": "uuid",
      "datasource_id": "uuid",
      "datasource_name": "生产数据CK",
      "question": "查询昨天销售额前10的产品",
      "generated_sql": "SELECT ...",
      "final_sql": "SELECT ...",
      "executed": true,
      "result_rows": 10,
      "execution_time": 0.5,
      "created_at": "2026-06-30T10:00:00Z"
    }
  ]
}
```

---

## 2. DataSource API（数据源管理接口）

### 2.1 获取数据源列表

**GET** `/datasources/list`

获取所有已配置的数据源。

**Response:**
```json
{
  "total": 3,
  "items": [
    {
      "id": "uuid",
      "name": "生产数据CK",
      "type": "clickhouse",
      "host": "10.1.2.3",
      "port": 9000,
      "database": "analytics_db",
      "username": "default",
      "is_active": true,
      "tables_count": 25,
      "created_at": "2026-06-30T09:00:00Z"
    }
  ]
}
```

---

### 2.2 添加数据源

**POST** `/datasources/add`

添加新的数据源配置。

**Request:**
```json
{
  "name": "生产数据CK",
  "type": "clickhouse",
  "host": "10.1.2.3",
  "port": 9000,
  "username": "default",
  "password": "your_password",
  "database": "analytics_db"
}
```

**Response:**
```json
{
  "id": "uuid",
  "message": "Datasource added successfully",
  "tables_extracted": 25,
  "ddl_trained": true
}
```

---

### 2.3 更新数据源

**PUT** `/datasources/{id}`

更新数据源配置。

**Request:**
```json
{
  "name": "生产数据CK（更新）",
  "host": "10.1.2.4",
  "password": "new_password"
}
```

**Response:**
```json
{
  "id": "uuid",
  "message": "Datasource updated successfully"
}
```

---

### 2.4 删除数据源

**DELETE** `/datasources/{id}`

删除数据源及其相关训练数据。

**Response:**
```json
{
  "id": "uuid",
  "message": "Datasource deleted successfully",
  "training_data_removed": 15
}
```

---

### 2.5 测试数据源连接

**POST** `/datasources/{id}/test`

测试数据源连接是否正常。

**Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "tables_count": 25,
  "response_time": 0.1  // seconds
}
```

---

### 2.6 获取表结构列表

**GET** `/datasources/{id}/tables`

获取数据源中所有表的结构信息。

**Query Parameters:**
- `limit` (optional): 返回数量，默认 50

**Response:**
```json
{
  "total": 25,
  "items": [
    {
      "table_name": "orders",
      "columns": [
        {"name": "id", "type": "Int32"},
        {"name": "product_name", "type": "String"},
        {"name": "amount", "type": "Float64"}
      ],
      "row_count": 1000000
    }
  ]
}
```

---

### 2.7 获取表 Schema

**GET** `/datasources/{id}/schema/{table_name}`

获取指定表的详细 schema 信息。

**Response:**
```json
{
  "table_name": "orders",
  "ddl": "CREATE TABLE orders (id Int32, product_name String, amount Float64) ENGINE = MergeTree() ORDER BY id",
  "columns": [
    {
      "name": "id",
      "type": "Int32",
      "nullable": false,
      "default": null,
      "comment": "订单ID"
    }
  ],
  "primary_key": "id",
  "indexes": []
}
```

---

## 3. Training API（训练数据管理接口）

### 3.1 获取训练数据列表

**GET** `/training/list`

获取所有训练数据。

**Query Parameters:**
- `datasource_id` (optional): 过滤特定数据源
- `source` (optional): manual / auto
- `is_approved` (optional): true / false
- `limit` (optional): 默认 50

**Response:**
```json
{
  "total": 100,
  "items": [
    {
      "id": "uuid",
      "datasource_id": "uuid",
      "datasource_name": "生产数据CK",
      "question": "查询昨天销售额前10的产品",
      "sql": "SELECT product_name, SUM(amount) FROM orders WHERE date = yesterday() GROUP BY product_name ORDER BY SUM(amount) DESC LIMIT 10",
      "source": "manual",
      "is_approved": true,
      "created_at": "2026-06-30T08:00:00Z"
    }
  ]
}
```

---

### 3.2 手动添加训练数据

**POST** `/training/add`

手动添加训练数据（问题-SQL对）。

**Request:**
```json
{
  "datasource_id": "uuid",
  "question": "查询昨天销售额前10的产品",
  "sql": "SELECT product_name, SUM(amount) FROM orders WHERE date = yesterday() GROUP BY product_name ORDER BY SUM(amount) DESC LIMIT 10"
}
```

**Response:**
```json
{
  "id": "uuid",
  "message": "Training data added successfully",
  "is_approved": true
}
```

---

### 3.3 编辑训练数据

**PUT** `/training/{id}`

编辑训练数据内容。

**Request:**
```json
{
  "question": "更新后的问题",
  "sql": "SELECT ..."
}
```

**Response:**
```json
{
  "id": "uuid",
  "message": "Training data updated successfully"
}
```

---

### 3.4 删除训练数据

**DELETE** `/training/{id}`

删除训练数据。

**Response:**
```json
{
  "id": "uuid",
  "message": "Training data deleted successfully"
}
```

---

### 3.5 标记为训练数据

**POST** `/training/auto-add`

将用户执行的 SQL 标记为训练数据。

**Request:**
```json
{
  "query_history_id": "uuid"
}
```

**Response:**
```json
{
  "id": "uuid",
  "message": "Training data marked for review",
  "is_approved": false
}
```

---

### 3.6 获取待审核训练数据

**GET** `/training/pending`

获取自动添加的待审核训练数据。

**Response:**
```json
{
  "total": 10,
  "items": [
    {
      "id": "uuid",
      "datasource_name": "生产数据CK",
      "question": "查询昨天的订单数量",
      "sql": "SELECT COUNT(*) FROM orders WHERE date = yesterday()",
      "created_at": "2026-06-30T10:00:00Z"
    }
  ]
}
```

---

### 3.7 审核通过训练数据

**POST** `/training/approve/{id}`

审核通过自动添加的训练数据。

**Response:**
```json
{
  "id": "uuid",
  "message": "Training data approved successfully",
  "is_approved": true
}
```

---

## 4. Settings API（系统配置接口）

### 4.1 获取系统配置

**GET** `/settings/config`

获取当前系统配置。

**Response:**
```json
{
  "minimax_endpoint": "http://10.242.52.62:9924",
  "minimax_model": "MiniMax-M2.7",
  "sql_timeout": 60,
  "max_result_rows": 1000,
  "auto_train_enabled": true,
  "log_level": "INFO"
}
```

---

### 4.2 更新系统配置

**PUT** `/settings/config`

更新系统配置。

**Request:**
```json
{
  "sql_timeout": 120,
  "max_result_rows": 5000
}
```

**Response:**
```json
{
  "message": "Configuration updated successfully",
  "updated_fields": ["sql_timeout", "max_result_rows"]
}
```

---

## 5. Health API（健康检查接口）

**GET** `/health`

检查所有服务健康状态。

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "backend_api": "healthy",
    "vanna_service": "healthy",
    "postgres": "healthy",
    "chromadb": "healthy"
  },
  "timestamp": "2026-06-30T10:00:00Z"
}
```

---

## API 文档访问

FastAPI 自动生成交互式 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 更新日期

2026-06-30