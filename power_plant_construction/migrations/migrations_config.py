import os

from pydantic import BaseSettings


class MigrationsConfig(BaseSettings):

    DB_NAME: str
    DB_HOSTS: str
    DB_PORT: str
    DB_PASSWORD: str
    DB_USER: str

    class Config:
        env_file = os.environ.get("ENV_PATH")
        case_sensitive = True
