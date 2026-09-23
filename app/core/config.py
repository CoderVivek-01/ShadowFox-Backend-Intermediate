"""
Application Configuration Module
Reads configuration from environment variables or .env file using Pydantic Settings.
"""

from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "NovaMart E-Commerce & Inventory API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "novamart_jwt_secret_key_intermediate_shadowfox_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./novamart.db"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "*"

    # Environment
    ENVIRONMENT: str = "development"

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            if self.CORS_ORIGINS.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
