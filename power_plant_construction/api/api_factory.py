import logging

from asyncpg import create_pool as create_db_pool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from event_sourcing.event_store_client import EventStoreClient
from power_plant_construction.api.api_config import ApiConfig, get_api_config
from power_plant_construction.api.auth import router as auth_router
from power_plant_construction.api.resources import notifications, tasks
from power_plant_construction.db import env_to_dsn, set_db_pool
from power_plant_construction.event_store import set_event_store

log = logging.getLogger(__name__)


class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return (
            record.getMessage().find("/api/healthcheck") == -1 and record.getMessage().find("/metrics") == -1
        )


def create_api(api_config: ApiConfig | None = None) -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
    )
    logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

    log.info("Creating api")

    if api_config is None:
        api_config = get_api_config()

    api = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    api.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
    )
    api.include_router(auth_router, prefix="/api/auth", tags=["auth"])

    log.info("Registering routes")
    for module in (tasks, notifications):
        uri_resource = module.__name__.split(".")[-1].replace("_", "-")
        api.include_router(
            module.router,
            prefix=f"/api/{uri_resource}",
            tags=[uri_resource],
        )

    db_dsn = env_to_dsn(
        user=api_config.DB_USER,
        password=api_config.DB_PASSWORD,
        hosts=api_config.DB_HOSTS,
        port=api_config.DB_PORT,
        name=api_config.DB_NAME,
    )

    async def init_database() -> None:
        log.info("Initializing db ...")
        db_pool = await create_db_pool(db_dsn)

        if not db_pool:
            raise Exception("Failed to connect to db")

        await set_db_pool(db_pool=db_pool)
        log.info("Initializing db [done]")

    async def init_event_store() -> None:
        log.info("Initializing event store ...")
        event_store = EventStoreClient(
            nats_dsn=api_config.NATS_DSN if api_config else "",
            event_types=set(),
        )
        await event_store.connect()
        set_event_store(event_store)
        log.info("Initializing event store and rpc relay [done]")

    log.info("Signalling startup")
    api.on_event("startup")(init_database)
    api.on_event("startup")(init_event_store)
    return api
