# 安全注意事项

## 安全架构概述

本项目定位为团队内部工具，当前设计无用户认证，依赖内网环境的安全性。所有服务在 Docker 网络内通信，仅暴露必要端口。

---

## 关键安全配置

### 1. 数据源密码加密

**问题：** PostgreSQL 中存储的数据源密码需要加密存储。

**解决方案：**

```python
# backend/app/utils/crypto.py

from cryptography.fernet import Fernet
import os

# 从环境变量获取加密密钥
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-default-key')

cipher = Fernet(ENCRYPTION_KEY)

def encrypt_password(password: str) -> str:
    """加密密码"""
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted: str) -> str:
    """解密密码"""
    return cipher.decrypt(encrypted.encode()).decode()
```

**配置步骤：**

```bash
# 1. 生成加密密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. 将密钥添加到 .env 文件
ENCRYPTION_KEY=your-generated-key-here

# 3. 在数据源模型中使用加密
class DataSource:
    password: str  # 存储加密后的密码
    
    def set_password(self, raw_password):
        self.password = encrypt_password(raw_password)
    
    def get_password(self):
        return decrypt_password(self.password)
```

---

### 2. MiniMax API Key 保护

**问题：** MiniMax API Key 需要妥善保管，避免泄露。

**解决方案：**

**存储方式：**
- API Key 存储在 `.env` 文件中
- `.env` 文件不要提交到 Git（已在 `.gitignore`）
- 使用环境变量传递给容器

**配置：**

```bash
# .env 文件（不提交到 Git）
MINIMAX_API_KEY=your-api-key-here

# .gitignore
.env
.env.local
*.key
```

**传递方式：**

```yaml
# docker-compose.yml
services:
  vanna-service:
    environment:
      - MINIMAX_API_KEY=${MINIMAX_API_KEY}  # 从环境变量读取
```

**安全检查：**

```bash
# 确保 .env 文件不在 Git 中
git status | grep .env  # 应该没有输出

# 检查容器内的环境变量（仅调试）
docker-compose exec vanna-service printenv | grep MINIMAX
```

---

### 3. 内部网络安全

**当前设计：**

- 所有服务在 `text2sql-network` 桥接网络内通信
- Frontend 对外暴露端口 3000
- Backend API 对外暴露端口 8000
- Vanna Service 和 PostgreSQL 不对外暴露（可选）

**加固建议：**

```yaml
# docker-compose.yml - 不对外暴露内部服务
services:
  vanna-service:
    ports:
      - "8001:8001"  # 仅用于调试，生产环境可删除
      
  postgres:
    ports:
      - "5432:5432"  # 仅用于调试，生产环境可删除
```

**网络隔离：**

```yaml
# 创建独立的内部网络
networks:
  text2sql-internal:
    driver: bridge
    internal: true  # 完全隔离，不对外通信
  
  text2sql-external:
    driver: bridge

services:
  frontend:
    networks:
      - text2sql-external
  
  backend-api:
    networks:
      - text2sql-external
      - text2sql-internal
  
  vanna-service:
    networks:
      - text2sql-internal
  
  postgres:
    networks:
      - text2sql-internal
```

---

### 4. 无认证风险评估

**当前状态：**
- 无用户认证机制
- 任何能访问 http://localhost:3000 的用户都能使用所有功能
- 可以访问所有数据源，执行任意 SQL

**适用场景：**
- 内网环境（办公网络）
- 团队内部使用（信任所有团队成员）
- 不对外公开访问

**不适用场景：**
- 公网环境
- 多团队共享（需要权限隔离）
- 包含敏感数据源

**如果需要认证，可添加：**

**方案 1：简单认证（HTTP Basic Auth）**

```python
# backend/app/auth.py

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    # 简单的用户名密码验证
    if credentials.username != "admin" or credentials.password != "password":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username
```

**方案 2：JWT 认证**

```python
# backend/app/auth.py

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

def authenticate(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

## 安全风险清单

### 1. SQL 注入风险

**风险描述：**
生成的 SQL 可能包含注入风险，特别是如果用户手动修改 SQL。

**缓解措施：**

```python
# backend/app/services/sql_validator.py

import re

def validate_sql(sql: str) -> bool:
    """验证 SQL 是否安全"""
    
    # 禁止的危险操作
    dangerous_patterns = [
        r'DROP\s+TABLE',
        r'DROP\s+DATABASE',
        r'DELETE\s+FROM',  # 无 WHERE 的 DELETE
        r'TRUNCATE',
        r'INSERT\s+INTO',
        r'UPDATE\s+\w+\s+SET',  # 无 WHERE 的 UPDATE
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sql, re.IGNORECASE):
            return False
    
    return True

# 在执行 SQL 前验证
if not validate_sql(sql):
    raise HTTPException(status_code=400, detail="SQL contains dangerous operations")
```

---

### 2. 数据泄露风险

**风险描述：**
用户可能执行大量数据查询，导致敏感数据泄露。

**缓解措施：**

- 限制返回行数（默认 1000 行）
- 查询超时限制（默认 60 秒）
- 记录所有查询历史（审计）

```python
# backend/app/config.py

class Config:
    MAX_RESULT_ROWS = 1000  # 最大返回行数
    SQL_TIMEOUT = 60  # SQL 执行超时（秒）
    LOG_ALL_QUERIES = True  # 记录所有查询
```

---

### 3. 数据源连接信息泄露

**风险描述：**
数据源配置（host、username、password）可能泄露。

**缓解措施：**

- 密码加密存储
- API 响应不返回密码字段
- 日志中不记录敏感信息

```python
# backend/app/routers/datasources.py

@app.get("/datasources/list")
async def list_datasources():
    datasources = db.query(DataSource).all()
    
    # 不返回密码字段
    return [{
        "id": ds.id,
        "name": ds.name,
        "host": ds.host,
        "port": ds.port,
        "username": ds.username,
        # 不包含 password
        "database": ds.database,
    }]
```

---

### 4. ChromaDB 数据泄露

**风险描述：**
训练数据和 DDL 信息存储在 ChromaDB，可能包含敏感信息。

**缓解措施：**

- ChromaDB 容器不对外暴露端口
- Volume 持久化数据，定期备份
- 容器重启数据不丢失

---

### 5. 日志敏感信息

**风险描述：**
日志可能包含敏感信息（密码、SQL、查询结果）。

**缓解措施：**

```python
# backend/app/utils/logger.py

import logging

class SensitiveDataFilter(logging.Filter):
    """过滤敏感数据"""
    
    SENSITIVE_KEYWORDS = ['password', 'api_key', 'secret', 'token']
    
    def filter(self, record):
        msg = record.getMessage()
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in msg.lower():
                # 替换敏感信息
                msg = msg.replace(keyword, '[REDACTED]')
        record.msg = msg
        return True

# 配置日志过滤器
logger = logging.getLogger(__name__)
logger.addFilter(SensitiveDataFilter())
```

---

## 安全最佳实践

### 1. 环境隔离

```bash
# 开发环境
.env.development

# 生产环境
.env.production

# 测试环境
.env.test
```

### 2. 访问控制

如果需要添加访问控制：

```python
# 白名单 IP
ALLOWED_IPS = ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']

# 在 FastAPI 中检查
from fastapi import Request

@app.middleware("http")
async def check_ip(request: Request, call_next):
    client_ip = request.client.host
    if not ip_in_whitelist(client_ip):
        raise HTTPException(status_code=403, detail="IP not allowed")
    return await call_next(request)
```

### 3. 审计日志

```python
# 记录所有关键操作
def log_audit(action: str, user: str, details: dict):
    audit_log = {
        'action': action,
        'user': user,
        'details': details,
        'timestamp': datetime.now(),
        'ip': get_client_ip(),
    }
    db.add(AuditLog(**audit_log))
    db.commit()
```

### 4. 定期安全检查

```bash
# 检查依赖包安全漏洞
pip install safety
safety check

# 检查 Docker 镜像安全
docker scan text2sql-backend:latest

# 检查环境变量泄露
git log --all --full-history -- '*.env'
```

---

## 安全配置检查清单

部署前请检查：

- ✅ `.env` 文件不在 Git 中
- ✅ MiniMax API Key 正确配置
- ✅ 数据源密码加密存储
- ✅ SQL 执行有超时限制
- ✅ 结果返回有行数限制
- ✅ 危险 SQL 操作被禁止
- ✅ 内部服务不对外暴露
- ✅ 日志不包含敏感信息
- ✅ 查询历史有审计记录
- ✅ ChromaDB 数据定期备份
- ✅ PostgreSQL 数据定期备份

---

## 生产环境安全建议

如果要在生产环境部署：

### 1. 添加用户认证

- 使用 JWT 或 OAuth2
- 用户登录机制
- Session 管理

### 2. 权限控制

- 数据源权限分级
- 不同用户访问不同数据源
- SQL 执行权限控制

### 3. 网络安全

- HTTPS 加密传输
- 防火墙规则
- VPN 或内网访问

### 4. 监控和告警

- 异常查询监控
- 大数据量导出告警
- 失败查询记录

### 5. 数据加密

- 数据库连接加密（SSL）
- 敏感数据加密存储
- 传输加密

---

## 更新日期

2026-06-30