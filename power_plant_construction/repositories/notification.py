from typing import Mapping, Optional

from asyncpg.pool import PoolConnectionProxy

from event_sourcing.entity import EntityEvent
from power_plant_construction.entities.notification import (
    Notification,
    NotificationCreated,
    NotificationStatusUpdated,
)


class NotificationRepo:
    @staticmethod
    def _record_to_notification(record: Mapping) -> Notification:

        return Notification(
            entity_id=record["entity_id"],
            title=record["title"],
            content=record["content"],
            status=record["status"],
            receiver=record["receiver"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )

    async def fetch_by_id(self, conn: PoolConnectionProxy, *, entity_id: str) -> Optional[Notification]:
        notification_record = await conn.fetchrow(
            "select * from notifications where entity_id=$1",
            entity_id,
        )
        if not notification_record:
            return None

        return self._record_to_notification(notification_record)

    async def fetch_all_for_receiver(self, conn: PoolConnectionProxy, receiver: str) -> list[Notification]:
        notification_records = await conn.fetch(
            "select * from notifications where receiver=$1",
            receiver,
        )
        if not notification_records:
            return []

        return [
            self._record_to_notification(notification_record) for notification_record in notification_records
        ]

    async def persist(self, conn: PoolConnectionProxy, batch: list[EntityEvent]) -> None:
        for event in batch:
            if isinstance(event, NotificationCreated):
                await conn.execute(
                    """insert into notifications
                        (
                            entity_id,
                            title,
                            content,
                            status,
                            receiver
                        )
                        values ($1, $2, $3, $4, $5)
                    """,
                    event.entity_id,
                    event.title,
                    event.content,
                    event.status,
                    event.receiver,
                )
            elif isinstance(event, NotificationStatusUpdated):
                await conn.execute(
                    """update notifications
                        set
                            status = $2,
                            updated_at = (now() at time zone 'utc')
                        where entity_id = $1
                    """,
                    event.entity_id,
                    event.status,
                )
            else:
                raise AssertionError()


_NOTIFICATION_REPO: NotificationRepo | None = None


def get_notification_repo() -> NotificationRepo:
    global _NOTIFICATION_REPO  # pylint: disable=global-statement
    if _NOTIFICATION_REPO is None:
        _NOTIFICATION_REPO = NotificationRepo()

    return _NOTIFICATION_REPO
