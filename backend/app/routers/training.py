# backend/app/routers/training.py

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.training import TrainingData

router = APIRouter(prefix="/training", tags=["training"])


class TrainingAdd(BaseModel):
    datasource_id: uuid.UUID
    question: str
    sql: str


class TrainingUpdate(BaseModel):
    question: Optional[str] = None
    sql: Optional[str] = None


class MarkAsTraining(BaseModel):
    query_history_id: uuid.UUID


def _serialize_training(td) -> dict:
    return {
        "id": str(td.id),
        "datasource_id": str(td.datasource_id),
        "question": td.question,
        "sql": td.sql,
        "source": td.source,
        "is_approved": td.is_approved,
        "created_at": td.created_at.isoformat() if td.created_at else None,
    }


@router.get("/list")
def list_training(
    datasource_id: Optional[uuid.UUID] = None,
    source: Optional[str] = None,
    is_approved: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """获取训练数据列表"""
    stmt = select(TrainingData)
    if datasource_id is not None:
        stmt = stmt.where(TrainingData.datasource_id == datasource_id)
    if source is not None:
        stmt = stmt.where(TrainingData.source == source)
    if is_approved is not None:
        stmt = stmt.where(TrainingData.is_approved == is_approved)
    stmt = stmt.order_by(TrainingData.created_at.desc()).offset(offset).limit(limit)
    items = list(db.scalars(stmt).all())

    total_stmt = select(func.count(TrainingData.id))
    if datasource_id is not None:
        total_stmt = total_stmt.where(TrainingData.datasource_id == datasource_id)
    if source is not None:
        total_stmt = total_stmt.where(TrainingData.source == source)
    if is_approved is not None:
        total_stmt = total_stmt.where(TrainingData.is_approved == is_approved)
    total = db.scalar(total_stmt) or 0

    return {"total": total, "items": [_serialize_training(td) for td in items]}


@router.post("/add")
def add_training(body: TrainingAdd, db: Session = Depends(get_db)):
    """手动添加训练数据"""
    td = TrainingData(
        datasource_id=body.datasource_id,
        question=body.question,
        sql=body.sql,
        source="manual",
        is_approved=True,
    )
    db.add(td)
    db.commit()
    db.refresh(td)
    return {
        "id": str(td.id),
        "message": "Training data added successfully",
        "is_approved": True,
    }


@router.put("/{training_id}")
def update_training(
    training_id: uuid.UUID, body: TrainingUpdate, db: Session = Depends(get_db)
):
    """编辑训练数据"""
    td = db.get(TrainingData, training_id)
    if td is None:
        raise HTTPException(status_code=404, detail="Training data not found")
    if body.question is not None:
        td.question = body.question
    if body.sql is not None:
        td.sql = body.sql
    db.commit()
    db.refresh(td)
    return {"id": str(td.id), "message": "Training data updated successfully"}


@router.delete("/{training_id}")
def delete_training(training_id: uuid.UUID, db: Session = Depends(get_db)):
    """删除训练数据"""
    td = db.get(TrainingData, training_id)
    if td is None:
        raise HTTPException(status_code=404, detail="Training data not found")
    db.delete(td)
    db.commit()
    return {"id": str(training_id), "message": "Training data deleted successfully"}


@router.post("/auto-add")
def mark_as_training(body: MarkAsTraining, db: Session = Depends(get_db)):
    """将查询历史标记为训练数据"""
    raise HTTPException(
        status_code=501, detail="Auto-add training not yet implemented"
    )


@router.get("/pending")
def get_pending_training(db: Session = Depends(get_db)):
    """获取待审核训练数据"""
    stmt = (
        select(TrainingData)
        .where(TrainingData.is_approved == False, TrainingData.source == "auto")
        .order_by(TrainingData.created_at.desc())
    )
    items = list(db.scalars(stmt).all())
    return {"total": len(items), "items": [_serialize_training(td) for td in items]}


@router.post("/approve/{training_id}")
def approve_training(training_id: uuid.UUID, db: Session = Depends(get_db)):
    """审核通过训练数据"""
    td = db.get(TrainingData, training_id)
    if td is None:
        raise HTTPException(status_code=404, detail="Training data not found")
    td.is_approved = True
    db.commit()
    db.refresh(td)
    return {
        "id": str(td.id),
        "message": "Training data approved successfully",
        "is_approved": True,
    }
