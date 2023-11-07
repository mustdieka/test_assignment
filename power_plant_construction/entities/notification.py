from datetime import datetime
from typing import Any, Union

from contracts.schemas.notification import NotificationStatus
from event_sourcing.entity import Entity, EntityEvent


class NotificationCreated(EntityEvent):
    __entity_type__ = "Notification"

    def __init__(
        self,
        *,
        entity_id: str,
        title: str,
        content: str,
        status: NotificationStatus,
        receiver: str,
        event_created_at: datetime | None = None,
        published_at: datetime | None = None,
    ) -> None:
        super().__init__(event_created_at=event_created_at, published_at=published_at, entity_id=entity_id)
        self._title = title
        self._content = content
        self._status = status
        self._receiver = receiver

    def body(self) -> dict[str, Any]:
        return {
            "title": self._title,
            "content": self._content,
            "status": self._status,
            "receiver": self._receiver,
        }

    @property
    def title(self) -> str:
        return self._title

    @property
    def content(self) -> str:
        return self._content

    @property
    def status(self) -> NotificationStatus:
        return self._status

    @property
    def receiver(self) -> str:
        return self._receiver


class NotificationStatusUpdated(EntityEvent):
    __entity_type__ = "Notification"

    def __init__(
        self,
        *,
        entity_id: str,
        status: NotificationStatus,
        event_created_at: datetime | None = None,
        published_at: datetime | None = None,
    ) -> None:
        super().__init__(event_created_at=event_created_at, published_at=published_at, entity_id=entity_id)
        self._status = status

    def body(self) -> dict[str, Any]:
        return {
            "status": self._status,
        }

    @property
    def status(self) -> NotificationStatus:
        return self._status


class Notification(Entity):
    AGGREGATE_EVENT_TYPES = Union[NotificationCreated, NotificationStatusUpdated]

    def __init__(
        self,
        *,
        entity_id: str,
        title: str,
        content: str,
        status: NotificationStatus,
        receiver: str,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__(entity_id=entity_id, created_at=created_at, updated_at=updated_at)
        self._title = title
        self._content = content
        self._status = status
        self._receiver = receiver

    def mark_read(self) -> None:
        self._status = NotificationStatus.READ
        self._batch.append(
            NotificationStatusUpdated(
                entity_id=self.entity_id,
                status=self._status,
            )
        )

    @property
    def title(self) -> str:
        return self._title

    @property
    def content(self) -> str:
        return self._content

    @property
    def status(self) -> NotificationStatus:
        return self._status

    @property
    def receiver(self) -> str:
        return self._receiver

    @classmethod
    def new(
        cls,
        *,
        entity_id: str,
        title: str,
        content: str,
        receiver: str,
    ) -> "Notification":
        notification = Notification(
            entity_id=entity_id,
            title=title,
            content=content,
            status=NotificationStatus.UNREAD,
            receiver=receiver,
        )
        notification._batch.append(
            NotificationCreated(
                entity_id=entity_id,
                title=title,
                content=content,
                status=NotificationStatus.UNREAD,
                receiver=receiver,
            )
        )

        return notification
