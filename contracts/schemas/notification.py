from datetime import datetime
from enum import Enum, unique

from pydantic import BaseModel, Extra


@unique
class NotificationStatus(str, Enum):
    UNREAD = "UNREAD"
    READ = "READ"


class NotificationDto(BaseModel, extra=Extra.forbid):
    id: str
    title: str
    content: str
    status: NotificationStatus
    created_at: datetime
    updated_at: datetime
