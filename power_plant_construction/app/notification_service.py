from typing import Callable, Type
from uuid import uuid4
import logging

from asyncpg import Pool

from event_sourcing.entity import EntityEvent
from event_sourcing.event_store_client import EventStoreClient
from power_plant_construction.commands.notification.create import Create as NotificationCreate
from power_plant_construction.entities.task import TaskCreated, TaskStatusUpdated
from power_plant_construction.repositories.notification import get_notification_repo

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class NotificationService:
    def __init__(self, event_store: EventStoreClient, db_pool: Pool) -> None:
        self._event_store = event_store
        self._pool = db_pool
        self.__notification_repo = get_notification_repo()
        self._event_handlers: dict[Type, Callable] = {
            TaskCreated: self.handle_task_created,
            TaskStatusUpdated: self.handle_task_updated,
        }

    async def handle_event(self, event: EntityEvent) -> None:
        handler = self._event_handlers.get(type(event))
        if handler is not None:
            await handler(event)

    async def handle_task_created(self, event: TaskCreated) -> None:
        log.info(f"Sending notification in response to task {event.title} being created")
        notification_create = NotificationCreate(
            command_id=str(uuid4()),
            principal_id=str(uuid4()),
            title=f"New task: {event.title}",
            content=f"Please do the following task:\n----\n{event.description}",
            receiver=event.assignee,
        )
        await notification_create.execute(
            pool=self._pool, event_store=self._event_store, notification_repo=self.__notification_repo
        )

    async def handle_task_updated(self, event: TaskStatusUpdated) -> None:
        log.info(f"Sending notification in response to task {event.entity_id} being completed")

        notification_create = NotificationCreate(
            command_id=str(uuid4()),
            principal_id=str(uuid4()),
            title=f"Task: {event.entity_id} has been completed",
            content="Please review the completed task",
            receiver=event.author,
        )
        await notification_create.execute(
            pool=self._pool, event_store=self._event_store, notification_repo=self.__notification_repo
        )
