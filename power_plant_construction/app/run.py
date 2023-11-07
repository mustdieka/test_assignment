import asyncio
import logging

from asyncpg import create_pool as create_db_pool

from event_sourcing.event_store_client import EventStoreClient, EventStoreSubscription
from power_plant_construction.app.app_config import AppConfig, get_app_config
from power_plant_construction.app.notification_service import NotificationService
from power_plant_construction.db import env_to_dsn
from power_plant_construction.entities.task import Task, TaskCreated, TaskStatusUpdated

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


async def run_app(app_config: AppConfig | None = None) -> None:
    log.info("Starting services app")
    if app_config is None:
        app_config = get_app_config()

    db_dsn = env_to_dsn(
        user=app_config.DB_USER,
        password=app_config.DB_PASSWORD,
        hosts=app_config.DB_HOSTS,
        port=app_config.DB_PORT,
        name=app_config.DB_NAME,
    )

    event_store = EventStoreClient(
        event_types={TaskCreated, TaskStatusUpdated},
        nats_dsn=app_config.NATS_DSN,
    )
    log.info("Setting up db connection pool")
    db_pool = await create_db_pool(db_dsn, max_size=30)
    await event_store.connect()

    subscription = EventStoreSubscription(event_class="entity", entity_type=Task)

    notification_service = NotificationService(event_store=event_store, db_pool=db_pool)

    log.info(f"Listening to event store subscriptions: {subscription.nats_channel}...")

    async for event in event_store.subscribe(subscription):
        log.info(f"handling event: {event.entity_id}/{type(event).__name__}")
        try:
            await asyncio.gather(
                notification_service.handle_event(event),
            )
        except Exception:
            log.exception(f"Failed to process event: {event.event_id}/{type(event).__name__}")
            log.info(f"Event dump: {event.source_dump}")

    log.info("disconnecting..")
    await event_store.disconnect()
