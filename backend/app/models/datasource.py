# backend/app/models/datasource.py

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Datasource(Base):
    __tablename__ = "datasources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, comment="数据源名称")
    type = Column(String(50), nullable=False, comment="数据库类型: clickhouse/postgresql/mysql")
    host = Column(String(255), nullable=False, comment="主机地址")
    port = Column(Integer, nullable=False, comment="端口号")
    username = Column(String(255), nullable=False, comment="用户名")
    password = Column(Text, nullable=False, comment="加密后的密码")
    database = Column(String(255), nullable=False, comment="数据库名称")
    is_active = Column(Boolean, default=True, comment="是否启用")
    tables_count = Column(Integer, default=0, comment="表数量")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
