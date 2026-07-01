# backend/app/routers/datasource.py

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.datasource import DatasourceService

router = APIRouter(prefix="/datasources", tags=["datasources"])


class DatasourceCreate(BaseModel):
    name: str
    type: str
    host: str
    port: int
    username: str
    password: str
    database: str


class DatasourceUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


def _serialize_datasource(ds) -> dict:
    """将 Datasource ORM 对象转为 API 响应 dict（脱敏密码）"""
    return {
        "id": str(ds.id),
        "name": ds.name,
        "type": ds.type,
        "host": ds.host,
        "port": ds.port,
        "database": ds.database,
        "username": ds.username,
        "is_active": ds.is_active,
        "tables_count": ds.tables_count,
        "created_at": ds.created_at.isoformat() if ds.created_at else None,
    }


@router.get("/list")
def list_datasources(db: Session = Depends(get_db)):
    """获取所有数据源"""
    service = DatasourceService(db)
    items = service.list_datasources()
    return {"total": len(items), "items": [_serialize_datasource(ds) for ds in items]}


@router.post("/add")
def add_datasource(body: DatasourceCreate, db: Session = Depends(get_db)):
    """添加数据源"""
    service = DatasourceService(db)
    try:
        ds = service.add_datasource(
            name=body.name,
            type=body.type,
            host=body.host,
            port=body.port,
            username=body.username,
            password=body.password,
            database=body.database,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection failed: {e}")
    return {
        "id": str(ds.id),
        "message": "Datasource added successfully",
        "tables_extracted": ds.tables_count,
        "ddl_trained": False,
    }


@router.put("/{datasource_id}")
def update_datasource(
    datasource_id: uuid.UUID, body: DatasourceUpdate, db: Session = Depends(get_db)
):
    """更新数据源"""
    service = DatasourceService(db)
    ds = service.update_datasource(
        datasource_id=datasource_id,
        name=body.name,
        host=body.host,
        port=body.port,
        username=body.username,
        password=body.password,
        is_active=body.is_active,
    )
    if ds is None:
        raise HTTPException(status_code=404, detail="Datasource not found")
    return {"id": str(ds.id), "message": "Datasource updated successfully"}


@router.delete("/{datasource_id}")
def delete_datasource(datasource_id: uuid.UUID, db: Session = Depends(get_db)):
    """删除数据源"""
    service = DatasourceService(db)
    result = service.delete_datasource(datasource_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Datasource not found")
    return {
        "id": str(datasource_id),
        "message": "Datasource deleted successfully",
        "training_data_removed": result["training_data_removed"],
    }


@router.post("/{datasource_id}/test")
def test_datasource(datasource_id: uuid.UUID, db: Session = Depends(get_db)):
    """测试数据源连接"""
    service = DatasourceService(db)
    result = service.test_connection(datasource_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/{datasource_id}/tables")
def get_tables(
    datasource_id: uuid.UUID, limit: int = 50, db: Session = Depends(get_db)
):
    """获取数据源表结构列表"""
    service = DatasourceService(db)
    try:
        tables = service.get_tables(datasource_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Datasource not found")
    except NotImplementedError:
        raise HTTPException(
            status_code=501, detail="Table extraction not yet implemented"
        )
    return {"total": len(tables), "items": tables[:limit]}


@router.get("/{datasource_id}/schema/{table_name}")
def get_table_schema(
    datasource_id: uuid.UUID, table_name: str, db: Session = Depends(get_db)
):
    """获取指定表 schema"""
    service = DatasourceService(db)
    try:
        schema = service.get_table_schema(datasource_id, table_name)
    except ValueError:
        raise HTTPException(status_code=404, detail="Datasource not found")
    except NotImplementedError:
        raise HTTPException(
            status_code=501, detail="Table schema extraction not yet implemented"
        )
    return schema
