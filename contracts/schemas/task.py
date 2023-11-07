from datetime import datetime
from enum import Enum, unique

from pydantic import BaseModel, Extra


@unique
class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class TaskDto(BaseModel, extra=Extra.forbid):
    id: str
    title: str
    description: str
    author: str
    assignee: str
    status: TaskStatus
    depends_on: list[str]
    created_at: datetime
    updated_at: datetime


class TaskCreateDto(BaseModel, extra=Extra.forbid):
    title: str
    description: str
    assignee: str


class TaskUpdateStatusDto(BaseModel, extra=Extra.forbid):
    status: TaskStatus


class TaskDependencyUpdateDto(BaseModel, extra=Extra.forbid):
    add: list[str]
    remove: list[str]
