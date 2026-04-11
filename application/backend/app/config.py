from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MOMPS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["development", "staging", "production"] = "development"
    api_secret: str = Field(default="dev-insecure", description="Shared secret for simple service auth")
    jwt_secret: str = Field(default="dev-jwt-insecure")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 12
    demo_username: str = "operator"
    demo_password: str = "demo"
    api_version: str = "v1"

    database_url: str = "postgresql+asyncpg://momps:momps_dev@localhost:5432/momps"

    influx_url: str = "http://localhost:8086"
    influx_token: str = ""
    influx_org: str = "momps"
    influx_bucket: str = "telemetry"

    rabbit_url: str = "amqp://momps:momps_dev@localhost:5672/"
    broker_backend: Literal["rabbitmq", "kafka"] = "rabbitmq"

    feature_cloud_sync: bool = False
    feature_cv_hook: bool = False
    feature_dem_simulation: bool = False
    feature_autonomy_hook: bool = True

    sim_tick_seconds: float = 2.0
    sim_terrain_width: int = 80
    sim_terrain_height: int = 80
    sim_cell_meters: float = 10.0

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
