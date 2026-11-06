"""读取 DEMO_ 环境变量；超时单位为秒，上传大小单位为字节。"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEMO_", env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/demo.db"
    broker_url: str = "redis://127.0.0.1:6379/0"
    session_seconds: int = Field(default=3600, ge=60, le=86400)
    upload_bytes: int = Field(default=65536, ge=1, le=65536)


@lru_cache
def settings():
    return Settings()
