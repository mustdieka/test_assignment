from collections import defaultdict
from typing import Mapping, Optional

from contracts.schemas.task import TaskStatus
from asyncpg.pool import PoolConnectionProxy

from event_sourcing.entity import EntityEvent
from power_plant_construction.entities.task import (
    Task,
    TaskCreated,
    TaskDependencyAdded,
    TaskDependencyRemoved,
    TaskStatusUpdated,
)


class TaskRepo:
    @staticmethod
    def _record_to_task(task_record: Mapping, *, depends_on: list[Mapping]) -> Task:
        return Task(
            entity_id=task_record["entity_id"],
            title=task_record["title"],
            description=task_record["description"],
            status=task_record["status"],
            assignee=task_record["assignee"],
            depends_on={record["depends_on"] for record in depends_on},
            author=task_record["author"],
            created_at=task_record["created_at"],
            updated_at=task_record["updated_at"],
        )

    async def fetch_by_id(self, conn: PoolConnectionProxy, *, entity_id: str) -> Optional[Task]:
        task_record = await conn.fetchrow(
            "select * from tasks where entity_id=$1",
            entity_id,
        )
        depends_on_records = await conn.fetch(
            "select * from task_dependencies where entity_id=$1",
            entity_id,
        )
        if not task_record:
            return None

        return self._record_to_task(task_record, depends_on=depends_on_records)

    async def fetch_by_assignee(self, conn: PoolConnectionProxy, *, assignee: str) -> list[Task]:
        task_dependency_records = await conn.fetch(
            "select * from tasks t join task_dependencies d on t.entity_id = d.entity_id where assignee=$1 ",
            assignee,
        )
        records_by_task_id: dict[str, list[Mapping]] = defaultdict(lambda: [])
        task_dependency_records = task_dependency_records or []
        for record in task_dependency_records:
            records_by_task_id[record["entity_id"]].append(record)

        return [
            self._record_to_task(depends_on[0], depends_on=depends_on)
            for depends_on in records_by_task_id.values()
        ]

    async def fetch_pending_unblocked_tasks(self, conn: PoolConnectionProxy, *, assignee: str) -> list[Task]:
        task_records = await conn.fetch(
            f"select * from tasks t1 where t1.status=$1 and t1.assignee=$2 "
            f"AND (NOT EXISTS "
            f"( SELECT * FROM task_dependencies t2 WHERE t1.entity_id = t2.entity_id AND t2.depends_on "
            f"NOT IN (SELECT entity_id FROM tasks WHERE status = $3)))", TaskStatus.PENDING,
            assignee, TaskStatus.COMPLETED
        )
        return [
            self._record_to_task(record, depends_on=[])
            for record in task_records
        ]

    async def persist(self, conn: PoolConnectionProxy, batch: list[EntityEvent]) -> None:
        for event in batch:
            if isinstance(event, TaskCreated):
                await conn.execute(
                    """insert into tasks
                        (
                            entity_id,
                            title,
                            description,
                            author,
                            assignee,
                            status
                        )
                        values ($1, $2, $3, $4, $5, $6)
                    """,
                    event.entity_id,
                    event.title,
                    event.description,
                    event.author,
                    event.assignee,
                    event.status,
                )
            elif isinstance(event, TaskDependencyAdded):
                await conn.execute(
                    """insert into task_dependencies
                        (
                            entity_id,
                            depends_on
                        )
                        values ($1, $2)
                    """,
                    event.entity_id,
                    event.depends_on,
                )
            elif isinstance(event, TaskDependencyRemoved):
                await conn.execute(
                    """delete from task_dependencies
                        where entity_id=$1 and depends_on=$2
                    """,
                    event.entity_id,
                    event.depends_on,
                )
            elif isinstance(event, TaskStatusUpdated):
                await conn.execute(
                    """update tasks
                        set status=$2
                        where entity_id=$1
                    """,
                    event.entity_id,
                    event.status,
                )
            else:
                print(event)
                print(type(event))
                raise AssertionError()


_TASK_REPO: TaskRepo | None = None


def get_task_repo() -> TaskRepo:
    global _TASK_REPO  # pylint: disable=global-statement
    if _TASK_REPO is None:
        _TASK_REPO = TaskRepo()

    return _TASK_REPO
