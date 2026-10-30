"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General
    app_name: str = "SentinelAI"
    environment: str = "development"
    secret_key: str = "change-me-to-a-long-random-string"
    access_token_expire_minutes: int = 60

    # Database
    postgres_user: str = "sentinel"
    postgres_password: str = "sentinel_secret"
    postgres_db: str = "sentinelai"
    postgres_host: str = "db"
    postgres_port: int = 5432
    database_url: str = ""

    # Hashing
    bcrypt_rounds: int = 12

    # Redis (optional)
    redis_url: str = "redis://redis:6379/0"

    # Monitoring
    network_monitor_enabled: bool = False
    monitor_interface: str = "any"
    monitor_allowed_cidrs: str = ""
    flow_idle_timeout: int = 60

    # ML
    ml_model_path: str = "ml/models/sentinel_model.joblib"
    ml_scaler_path: str = "ml/models/scaler.joblib"

    # Demo/seed
    seed_demo_data: bool = True
    seed_demo_events: int = 2000

    # Threat intelligence
    abuseipdb_api_key: str = ""
    virustotal_api_key: str = ""

    # AI assistant
    assistant_provider: str = "rules"  # "rules" or "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # CORS
    frontend_origin: str = "http://localhost:5173"

    @property
    def default_database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def get_database_url(self) -> str:
        return self.database_url or self.default_database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()