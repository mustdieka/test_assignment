from datetime import datetime

from asyncpg import Pool

from contracts.schemas.task import TaskStatus
from event_sourcing.entity import Command
from event_sourcing.event_store_client import EventStoreClient
from power_plant_construction.repositories.task import TaskRepo


class TaskNotFoundError(Exception):
    pass


class InvalidTaskStatusTransition(Exception):
    pass


class UpdateStatus(Command):
    def __init__(
        self,
        *,
        command_id: str,
        principal_id: str,
        status: TaskStatus,
        submitted_by: str,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(
            principal_id=principal_id,
            command_id=command_id,
            created_at=created_at,
        )
        self._status = status
        self._submitted_by = submitted_by

    async def execute(self, *, pool: Pool, event_store: EventStoreClient, task_repo: TaskRepo) -> None:
        async with pool.acquire() as conn:
            task = await task_repo.fetch_by_id(
                conn=conn,
                entity_id=self.principal_id,
            )
            if task is None:
                raise TaskNotFoundError()

            pending = self._status == TaskStatus.PENDING
            completed = task.status == TaskStatus.COMPLETED
            if pending or completed:
                raise InvalidTaskStatusTransition()

            if self._submitted_by not in (task.assignee, task.author):
                raise InvalidTaskStatusTransition()

            task.update_status(status=self._status)

            batch = task.drain()
            await task_repo.persist(conn, batch)

            await event_store.publish_batch(batch)
