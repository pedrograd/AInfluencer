from functools import lru_cache
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables with sane defaults."""

    api_host: str = Field(default="0.0.0.0", description="Host for FastAPI")
    api_port: int = Field(default=8000, description="Port for FastAPI")

    allowed_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ]
    )

    comfyui_server: str = Field(default="127.0.0.1:8188", description="ComfyUI host:port")
    database_url: str = Field(default="sqlite:///./ainfluencer.db")
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_password: Optional[str] = None

    demo_mode: bool = Field(default=False, description="Enforce CPU-friendly demo restrictions")
    enable_advanced: bool = Field(default=True)
    enable_upscale: bool = Field(default=True)
    enable_face_restore: bool = Field(default=True)
    enable_batch: bool = Field(default=True)
    enable_high_res: bool = Field(default=True)

    demo_max_width: int = Field(default=1024)
    demo_max_height: int = Field(default=1024)
    demo_max_batch: int = Field(default=1)

    rate_limiting_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=30)
    rate_limit_per_hour: int = Field(default=500)
    max_request_size_mb: int = Field(default=25)
    request_timeout_seconds: int = Field(default=120)
    max_concurrent_jobs: int = Field(default=1, description="Protect free tiers by serializing heavy jobs")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("allowed_origins", pre=True)
    def _split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

