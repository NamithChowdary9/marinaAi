"""
Application settings loaded from environment variables.
"""

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # OpenAI (optional fallback)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Google Gemini (free tier — preferred)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"

    # AIS
    aisstream_api_key: str = ""
    marinetraffic_api_key: str = ""

    # Weather
    openweather_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://marineai:password@localhost:5432/marineai_db"
    database_url_sync: str = "postgresql://marineai:password@localhost:5432/marineai_db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Security
    secret_key: str = "change-this-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 2000
    cors_origins_str: str = Field(
        default="http://localhost:1000,http://127.0.0.1:1000,http://localhost:1001,http://127.0.0.1:1001",
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins_str"),
    )

    # ML
    ml_models_dir: str = "./ml_models/saved"

    # WebSocket
    ws_heartbeat_interval: int = 30
    ship_update_interval: int = 60

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
