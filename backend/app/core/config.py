from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AINFLUENCER_", env_file=".env", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"
    comfyui_base_url: str = "http://localhost:8188"
    database_url: str = "postgresql+asyncpg://ainfluencer_user:password@localhost:5432/ainfluencer"


settings = Settings()
