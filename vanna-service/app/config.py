# vanna-service/app/config.py

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Vanna Service 配置"""

    # MiniMax API 配置
    minimax_endpoint: str = "http://10.242.52.62:9924"
    minimax_model: str = "MiniMax-M2.7"
    minimax_api_key: str

    # ChromaDB 配置
    chromadb_path: str = "/data/chromadb"

    # Service 配置
    service_name: str = "Vanna Service"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()
