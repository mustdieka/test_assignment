import os

from pydantic import BaseSettings


class AppConfig(BaseSettings):

    DB_NAME: str
    DB_HOSTS: str
    DB_PORT: str
    DB_PASSWORD: str
    DB_USER: str

    NATS_DSN: str = "nats://localhost:4222"

    class Config:
        env_file = os.environ.get("ENV_PATH")
        case_sensitive = True


_APP_CONFIG: AppConfig | None = None


def get_app_config() -> AppConfig:
    global _APP_CONFIG
    if _APP_CONFIG is None:
        _APP_CONFIG = AppConfig()

    return _APP_CONFIG
