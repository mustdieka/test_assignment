from datetime import datetime

from asyncpg import Pool

from event_sourcing.entity import Command
from event_sourcing.event_store_client import EventStoreClient
from power_plant_construction.entities.task import Task
from power_plant_construction.repositories.task import TaskRepo


class Create(Command):
    def __init__(
        self,
        *,
        command_id: str,
        principal_id: str,
        title: str,
        description: str,
        assignee: str,
        author: str,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(
            principal_id=principal_id,
            command_id=command_id,
            created_at=created_at,
        )
        self._title = title
        self._description = description
        self._assignee = assignee
        self._author = author

    async def execute(self, *, pool: Pool, event_store: EventStoreClient, task_repo: TaskRepo) -> None:
        async with pool.acquire() as conn:
            task = Task.new(
                entity_id=self._principal_id,
                title=self._title,
                description=self._description,
                assignee=self._assignee,
                author=self._author,
            )
            batch = task.drain()
            await task_repo.persist(conn, batch)

            await event_store.publish_batch(batch)
