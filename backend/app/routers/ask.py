# backend/app/routers/ask.py

import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.datasource import Datasource
from app.models.history import QueryHistory
from app.services.datasource import DatasourceService
from app.services.encryption import decrypt

router = APIRouter(prefix="/ask", tags=["ask"])


class GenerateSQLRequest(BaseModel):
    datasource_id: uuid.UUID
    question: str


class ExecuteSQLRequest(BaseModel):
    datasource_id: uuid.UUID
    sql: str
    timeout: Optional[int] = None


def _serialize_history(h) -> dict:
    return {
        "id": str(h.id),
        "datasource_id": str(h.datasource_id),
        "question": h.question,
        "generated_sql": h.generated_sql,
        "final_sql": h.final_sql,
        "executed": h.executed,
        "result_rows": h.result_rows,
        "execution_time": h.execution_time,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }


@router.post("/generate-sql")
def generate_sql(body: GenerateSQLRequest, db: Session = Depends(get_db)):
    """生成 SQL（调用 Vanna Service）"""
    ds = db.get(Datasource, body.datasource_id)
    if ds is None or not ds.is_active:
        raise HTTPException(
            status_code=404, detail="Datasource not found or inactive"
        )

    # 调用 Vanna Service
    try:
        service = DatasourceService(db)
        schema_context = service.build_schema_context(ds, body.question)
        with httpx.Client(timeout=settings.sql_timeout) as client:
            resp = client.post(
                f"{settings.vanna_service_url}/generate",
                json={
                    "question": body.question,
                    "datasource_name": ds.name,
                    "schema_context": schema_context,
                },
            )
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Vanna service error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Vanna 调用成功后再记录历史
    history = QueryHistory(
        datasource_id=body.datasource_id,
        question=body.question,
        generated_sql=result.get("data", {}).get("sql", result.get("sql", "")),
    )
    db.add(history)
    db.commit()

    data = result.get("data", result)
    return {
        "sql": data.get("sql", ""),
        "confidence": data.get("confidence", 0),
        "metrics": data.get("metrics", {}),
        "related_training_data": data.get(
            "related_training_data", data.get("similar_questions", [])
        ),
    }


@router.post("/execute-sql")
def execute_sql(body: ExecuteSQLRequest, db: Session = Depends(get_db)):
    """执行 SQL 并返回结果"""
    ds = db.get(Datasource, body.datasource_id)
    if ds is None or not ds.is_active:
        raise HTTPException(
            status_code=404, detail="Datasource not found or inactive"
        )

    # 解密密码并执行
    plaintext_password = decrypt(ds.password)
    service = DatasourceService(db)
    try:
        result = service._execute_sql_direct(
            ds.type,
            ds.host,
            ds.port,
            ds.username,
            plaintext_password,
            ds.database,
            body.sql,
            body.timeout or settings.sql_timeout,
            settings.max_result_rows,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 执行成功后再记录历史
    history = QueryHistory(
        datasource_id=body.datasource_id,
        question="",
        final_sql=body.sql,
        executed=True,
        result_rows=result.get("row_count", 0),
        execution_time=result.get("execution_time", 0),
    )
    db.add(history)
    db.commit()

    return result


@router.get("/history")
def get_history(
    datasource_id: Optional[uuid.UUID] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """获取查询历史"""
    stmt = select(QueryHistory)
    if datasource_id is not None:
        stmt = stmt.where(QueryHistory.datasource_id == datasource_id)
    stmt = stmt.order_by(QueryHistory.created_at.desc()).offset(offset).limit(limit)
    items = list(db.scalars(stmt).all())

    total_stmt = select(func.count(QueryHistory.id))
    if datasource_id is not None:
        total_stmt = total_stmt.where(QueryHistory.datasource_id == datasource_id)
    total = db.scalar(total_stmt) or 0

    return {"total": total, "items": [_serialize_history(h) for h in items]}
