# backend/app/routers/settings.py

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models.config import SystemConfig

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    sql_timeout: Optional[int] = None
    max_result_rows: Optional[int] = None


@router.get("/config")
def get_config():
    """获取系统配置"""
    return {
        "sql_timeout": settings.sql_timeout,
        "max_result_rows": settings.max_result_rows,
        "log_level": settings.log_level,
    }


@router.put("/config")
def update_config(body: SettingsUpdate, db: Session = Depends(get_db)):
    """更新系统配置"""
    updated = []
    if body.sql_timeout is not None:
        _upsert_config(
            db, "sql_timeout", str(body.sql_timeout), "SQL 查询超时(秒)"
        )
        updated.append("sql_timeout")
    if body.max_result_rows is not None:
        _upsert_config(
            db, "max_result_rows", str(body.max_result_rows), "最大返回行数"
        )
        updated.append("max_result_rows")

    return {"message": "Configuration updated successfully", "updated_fields": updated}


def _upsert_config(db: Session, key: str, value: str, description: str):
    """插入或更新系统配置"""
    stmt = select(SystemConfig).where(SystemConfig.key == key)
    existing = db.scalar(stmt)
    if existing:
        existing.value = value
        existing.description = description
    else:
        config = SystemConfig(key=key, value=value, description=description)
        db.add(config)
    db.commit()
