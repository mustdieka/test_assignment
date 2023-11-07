from datetime import datetime

from asyncpg import Pool

from event_sourcing.entity import Command
from event_sourcing.event_store_client import EventStoreClient
from power_plant_construction.entities.notification import Notification
from power_plant_construction.repositories.notification import NotificationRepo


class NotificationCreationFailed(Exception):
    pass


class Create(Command):
    def __init__(
        self,
        *,
        command_id: str,
        principal_id: str,
        title: str,
        content: str,
        receiver: str,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(principal_id=principal_id, command_id=command_id, created_at=created_at)
        self._title = title
        self._content = content
        self._receiver = receiver

    async def execute(
        self,
        *,
        pool: Pool,
        event_store: EventStoreClient,
        notification_repo: NotificationRepo,
    ) -> None:
        async with pool.acquire() as conn:
            notification = Notification.new(
                entity_id=self._principal_id,
                title=self._title,
                content=self._content,
                receiver=self._receiver,
            )
            batch = notification.drain()
            await notification_repo.persist(conn, batch)

            await event_store.publish_batch(batch)
