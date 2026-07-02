# backend/app/models/history.py

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Boolean, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    datasource_id = Column(UUID(as_uuid=True), ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False, comment="数据源ID")
    question = Column(Text, nullable=False, comment="用户问题")
    generated_sql = Column(Text, comment="AI生成的SQL")
    final_sql = Column(Text, comment="最终执行的SQL")
    executed = Column(Boolean, default=False, comment="是否已执行")
    result_rows = Column(Integer, default=0, comment="结果行数")
    execution_time = Column(Float, comment="执行耗时(秒)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
