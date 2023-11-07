from datetime import datetime

from asyncpg import Pool

from event_sourcing.entity import Command
from event_sourcing.event_store_client import EventStoreClient
from power_plant_construction.repositories.task import TaskRepo


class TaskNotFoundError(Exception):
    pass


class DependencyNotFoundError(Exception):
    pass


class RemoveDependency(Command):
    def __init__(
        self, *, command_id: str, principal_id: str, task: str, created_at: datetime | None = None
    ) -> None:
        super().__init__(
            principal_id=principal_id,
            command_id=command_id,
            created_at=created_at,
        )
        self._task_id_to_be_removed = task

    async def execute(self, *, pool: Pool, event_store: EventStoreClient, task_repo: TaskRepo) -> None:
        async with pool.acquire() as conn:
            task = await task_repo.fetch_by_id(
                conn=conn,
                entity_id=self.principal_id,
            )

            task_to_be_removed = await task_repo.fetch_by_id(
                conn=conn,
                entity_id=self._task_id_to_be_removed,
            )

            if task is None or task_to_be_removed is None:
                raise TaskNotFoundError()

            if self._task_id_to_be_removed not in task.depends_on:
                raise DependencyNotFoundError()

            task.remove_dependency(task=self._task_id_to_be_removed)

            batch = task.drain()
            await task_repo.persist(conn, batch)

            await event_store.publish_batch(batch)
