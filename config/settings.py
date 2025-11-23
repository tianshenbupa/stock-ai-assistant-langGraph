from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    """应用配置管理"""

    # ========== DeepSeek API ==========
    DEEPSEEK_API_KEY: str
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    MODEL_NAME: str = "deepseek-chat"  # 添加这个字段
    TEMPERATURE: float = 0.7  # 添加这个字段

    # ========== RAG 配置 ==========
    VECTOR_STORE_PATH: str = "data/vector_store"
    PDF_DIRECTORY: str = "data/financial_reports"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # ========== LangGraph 配置 ==========
    CHECKPOINTS_PATH: str = "data/checkpoints"
    MAX_ITERATIONS: int = 10

    # ========== 服务器配置 ==========
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ========== CORS 配置 ==========
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def ensure_directories(self):
        """确保所有必要的目录存在"""
        Path(self.VECTOR_STORE_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.PDF_DIRECTORY).mkdir(parents=True, exist_ok=True)
        Path(self.CHECKPOINTS_PATH).mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()
settings.ensure_directories()