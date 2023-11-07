from datetime import datetime

from asyncpg import Pool

from event_sourcing.entity import Command
from event_sourcing.event_store_client import EventStoreClient
from power_plant_construction.repositories.notification import NotificationRepo


class NotificationNotFoundError(Exception):
    pass


class NotificationReceiverMismatch(Exception):
    pass


class MarkRead(Command):
    def __init__(
        self, *, command_id: str, principal_id: str, receiver: str, created_at: datetime | None = None
    ) -> None:
        super().__init__(
            principal_id=principal_id,
            command_id=command_id,
            created_at=created_at,
        )
        self._receiver = receiver

    async def execute(
        self, *, pool: Pool, event_store: EventStoreClient, notification_repo: NotificationRepo
    ) -> None:
        async with pool.acquire() as conn:
            notification = await notification_repo.fetch_by_id(conn, entity_id=self._principal_id)
            if not notification:
                raise NotificationNotFoundError()
            if notification.receiver != self._receiver:
                raise NotificationReceiverMismatch()
            notification.mark_read()
            batch = notification.drain()
            await notification_repo.persist(conn, batch)

            await event_store.publish_batch(batch)
