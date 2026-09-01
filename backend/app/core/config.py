from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for SparkSight."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SPARKSIGHT_")
    app_name: str = "SparkSight – Distributed Sales Analytics Platform"
    allowed_origins: str = "http://localhost:5173"
    data_path: str = "data/sales_transactions.csv"
    spark_master: str = "local[*]"

    @property
    def resolved_data_path(self) -> Path:
        configured = Path(self.data_path)
        if configured.is_absolute():
            return configured
        return Path(__file__).resolve().parents[3] / configured

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
