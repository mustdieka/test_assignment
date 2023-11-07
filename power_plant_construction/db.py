from urllib.parse import quote

from asyncpg import Pool

_DB_POOL: Pool | None = None


async def get_db_pool() -> Pool:
    if _DB_POOL is None:
        raise RuntimeError("DD pool was not initialized")

    return _DB_POOL


async def set_db_pool(db_pool: Pool) -> None:
    global _DB_POOL  # pylint: disable=global-statement
    if _DB_POOL is not None:
        raise RuntimeError("DB pool was already initialized")
    _DB_POOL = db_pool


def env_to_dsn(
    *, user: str, password: str, hosts: str, port: str, name: str, dialect: str = "postgres"
) -> str:
    return f"{dialect}://{user}:" f"{quote(password)}" f"@{hosts}:{port}" f"/{name}"
