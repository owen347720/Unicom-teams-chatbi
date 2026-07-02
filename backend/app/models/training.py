# backend/app/models/training.py

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class TrainingData(Base):
    __tablename__ = "training_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    datasource_id = Column(UUID(as_uuid=True), ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False, comment="数据源ID")
    question = Column(Text, nullable=False, comment="问题")
    sql = Column(Text, nullable=False, comment="SQL语句")
    source = Column(String(20), default="manual", comment="来源: manual/auto")
    is_approved = Column(Boolean, default=True, comment="是否已审核通过")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
