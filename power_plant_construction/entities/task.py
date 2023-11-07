from datetime import datetime
from typing import Any, Union

from contracts.schemas.task import TaskStatus
from event_sourcing.entity import Entity, EntityEvent


class TaskCreated(EntityEvent):
    __entity_type__ = "Task"

    def __init__(
        self,
        *,
        entity_id: str,
        title: str,
        description: str,
        status: TaskStatus,
        assignee: str,
        author: str,
        event_created_at: datetime | None = None,
        published_at: datetime | None = None,
    ) -> None:
        super().__init__(event_created_at=event_created_at, published_at=published_at, entity_id=entity_id)
        self._title = title
        self._description = description
        self._status = status
        self._assignee = assignee
        self._author = author

    def body(self) -> dict[str, Any]:
        return {
            "title": self._title,
            "description": self._description,
            "status": self._status,
            "assignee": self._assignee,
            "author": self._author,
        }

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def assignee(self) -> str:
        return self._assignee

    @property
    def author(self) -> str:
        return self._author


class TaskDependencyAdded(EntityEvent):
    __entity_type__ = "Task"

    def __init__(
        self,
        *,
        entity_id: str,
        depends_on: str,
        event_created_at: datetime | None = None,
        published_at: datetime | None = None,
    ) -> None:
        super().__init__(event_created_at=event_created_at, published_at=published_at, entity_id=entity_id)
        self._depends_on = depends_on

    def body(self) -> dict[str, Any]:
        return {"depends_on": self._depends_on}

    @property
    def depends_on(self) -> str:
        return self._depends_on


class TaskDependencyRemoved(EntityEvent):
    __entity_type__ = "Task"

    def __init__(
        self,
        *,
        entity_id: str,
        depends_on: str,
        event_created_at: datetime | None = None,
        published_at: datetime | None = None,
    ) -> None:
        super().__init__(event_created_at=event_created_at, published_at=published_at, entity_id=entity_id)
        self._depends_on = depends_on

    def body(self) -> dict[str, Any]:
        return {"depends_on": self._depends_on}

    @property
    def depends_on(self) -> str:
        return self._depends_on


class TaskStatusUpdated(EntityEvent):
    __entity_type__ = "Task"

    def __init__(
        self,
        *,
        entity_id: str,
        status: TaskStatus,
        author: str,
        event_created_at: datetime | None = None,
        published_at: datetime | None = None,
    ) -> None:
        super().__init__(event_created_at=event_created_at, published_at=published_at, entity_id=entity_id)
        self._status = status
        self._author = author

    def body(self) -> dict[str, Any]:
        return {
            "status": self._status,
            "author": self._author,
        }

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def author(self) -> str:
        return self._author


class Task(Entity):
    AGGREGATE_EVENT_TYPES = Union[TaskCreated, TaskStatusUpdated, TaskDependencyAdded, TaskDependencyRemoved]

    def __init__(
        self,
        *,
        entity_id: str,
        title: str,
        description: str,
        depends_on: set[str],
        status: TaskStatus,
        assignee: str,
        author: str,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__(entity_id=entity_id, created_at=created_at, updated_at=updated_at)
        self._title = title
        self._description = description
        self._status = status
        self._assignee = assignee
        self._author = author
        self._depends_on = depends_on

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def assignee(self) -> str:
        return self._assignee

    @property
    def author(self) -> str:
        return self._author

    @property
    def depends_on(self) -> set[str]:
        return self._depends_on

    def add_dependency(self, task: str) -> None:
        self._depends_on.add(task)
        self._batch.append(TaskDependencyAdded(entity_id=self.entity_id, depends_on=task))

    def remove_dependency(self, task: str) -> None:
        self._depends_on.remove(task)
        self._batch.append(TaskDependencyRemoved(entity_id=self.entity_id, depends_on=task))

    def update_status(self, status: TaskStatus) -> None:
        self._status = status
        self._batch.append(TaskStatusUpdated(entity_id=self.entity_id, status=status, author=self._author))

    @classmethod
    def new(
        cls,
        *,
        entity_id: str,
        title: str,
        description: str,
        assignee: str,
        author: str,
    ) -> "Task":
        initial_status = TaskStatus.PENDING
        task = Task(
            entity_id=entity_id,
            title=title,
            description=description,
            depends_on=set(),
            status=initial_status,
            assignee=assignee,
            author=author,
        )
        task._batch.append(
            TaskCreated(
                entity_id=entity_id,
                title=title,
                description=description,
                status=initial_status,
                assignee=assignee,
                author=author,
            )
        )

        return task
