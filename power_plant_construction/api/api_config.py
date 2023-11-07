import os

from pydantic import BaseSettings


class ApiConfig(BaseSettings):
    DB_NAME: str
    DB_HOSTS: str
    DB_PORT: str
    DB_PASSWORD: str
    DB_USER: str

    API_HOST: str = "0.0.0.0"
    API_PORT: str = "8080"

    NATS_DSN: str

    class Config:
        env_file = os.environ.get("ENV_PATH")
        case_sensitive = True


_API_CONFIG: ApiConfig | None = None


def get_api_config() -> ApiConfig:
    global _API_CONFIG
    if _API_CONFIG is None:
        _API_CONFIG = ApiConfig()

    return _API_CONFIG
