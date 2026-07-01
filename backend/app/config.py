# backend/app/config.py

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API 配置
    app_name: str = "Text2SQL Backend API"
    app_version: str = "1.0.0"

    # Vanna Service
    vanna_service_url: str = "http://vanna-service:8001"

    # PostgreSQL
    database_url: str = "postgresql://text2sql:text2sql123@postgres:5432/text2sql"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # SQL 配置
    sql_timeout: int = 60
    max_result_rows: int = 1000

    # 加密密钥
    encryption_key: str = "default-key-change-in-production"

    # 日志
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
