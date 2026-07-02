"""
Vanna Service - FastAPI 主应用
提供 REST API 端点用于 SQL 生成和训练
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.vanna_integration import VannaService

# 全局 VannaService 实例
vanna_service: Optional[VannaService] = None

# FastAPI 应用初始化
app = FastAPI(
    title="Vanna Service",
    version="1.0.0",
    description="SQL 生成和训练数据管理服务",
)

# 配置日志 - 根据环境使用不同路径
log_dir = os.environ.get("LOG_DIR", "/app/logs")
os.makedirs(log_dir, exist_ok=True)
logger.add(os.path.join(log_dir, "vanna.log"), rotation="1 day", retention="7 days", level="INFO")


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化 VannaService"""
    global vanna_service
    try:
        vanna_service = VannaService()
        logger.info("VannaService initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize VannaService: {e}")
        raise


# ============ Request Models ============

class TrainDDLRequest(BaseModel):
    """DDL 训练请求"""
    datasource_name: str
    ddl: str


class TrainSQLRequest(BaseModel):
    """SQL 训练请求"""
    datasource_name: str
    question: str
    sql: str


class GenerateSQLRequest(BaseModel):
    """SQL 生成请求"""
    datasource_name: str
    question: str
    schema_context: Optional[str] = None


# ============ Response Models ============

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str


class TrainDDLResponse(BaseModel):
    """DDL 训练响应"""
    success: bool
    message: str


class TrainSQLResponse(BaseModel):
    """SQL 训练响应"""
    success: bool
    message: str


class GenerateSQLData(BaseModel):
    """SQL 生成数据"""
    sql: str
    confidence: float
    similar_questions: list
    metrics: dict = {}


class GenerateSQLResponse(BaseModel):
    """SQL 生成响应"""
    success: bool
    data: GenerateSQLData


class SimilarDataResponse(BaseModel):
    """相似训练数据响应"""
    success: bool
    data: list


# ============ API Endpoints ============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查端点

    Returns:
        服务健康状态
    """
    return HealthResponse(
        status="healthy",
        service="Vanna Service",
        version="1.0.0"
    )


@app.post("/train/ddl", response_model=TrainDDLResponse)
async def train_ddl(request: TrainDDLRequest):
    """
    训练 DDL 信息

    Args:
        request: DDL 训练请求

    Returns:
        训练结果
    """
    try:
        vanna_service.train_ddl(
            datasource_name=request.datasource_name,
            ddl=request.ddl
        )
        logger.info(f"DDL trained for {request.datasource_name}")
        return TrainDDLResponse(
            success=True,
            message="DDL trained successfully"
        )
    except Exception as e:
        logger.error(f"DDL training failed: {e}")
        raise HTTPException(status_code=500, detail=f"DDL training failed: {str(e)}")


@app.post("/train/sql", response_model=TrainSQLResponse)
async def train_sql(request: TrainSQLRequest):
    """
    训练问题-SQL对

    Args:
        request: SQL 训练请求

    Returns:
        训练结果
    """
    try:
        vanna_service.train_sql(
            datasource_name=request.datasource_name,
            question=request.question,
            sql=request.sql
        )
        logger.info(f"SQL trained for {request.datasource_name}: {request.question}")
        return TrainSQLResponse(
            success=True,
            message="SQL trained successfully"
        )
    except Exception as e:
        logger.error(f"SQL training failed: {e}")
        raise HTTPException(status_code=500, detail=f"SQL training failed: {str(e)}")


@app.post("/generate", response_model=GenerateSQLResponse)
async def generate_sql(request: GenerateSQLRequest):
    """
    生成 SQL

    Args:
        request: SQL 生成请求

    Returns:
        生成的 SQL 和相关信息
    """
    try:
        result = vanna_service.generate_sql(
            datasource_name=request.datasource_name,
            question=request.question,
            schema_context=request.schema_context,
        )
        logger.info(f"SQL generated for {request.datasource_name}: {request.question}")
        return GenerateSQLResponse(
            success=True,
            data=GenerateSQLData(
                sql=result["sql"],
                confidence=result["confidence"],
                similar_questions=result["similar_questions"],
                metrics=result.get("metrics", {}),
            )
        )
    except Exception as e:
        logger.error(f"SQL generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"SQL generation failed: {str(e)}")


@app.get("/similar/{question}", response_model=SimilarDataResponse)
async def get_similar(question: str, n: int = 5):
    """
    获取相似训练数据

    Args:
        question: 查询问题
        n: 返回数量，默认 5

    Returns:
        相似训练数据列表
    """
    try:
        result = vanna_service.get_similar_training_data(question=question, n=n)
        logger.info(f"Similar training data retrieved for: {question}")
        return SimilarDataResponse(
            success=True,
            data=result
        )
    except Exception as e:
        logger.error(f"Similar data retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Similar data retrieval failed: {str(e)}")
