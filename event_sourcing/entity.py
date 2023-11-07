from abc import ABC, abstractmethod
from datetime import datetime
from logging import getLogger
from typing import Any, TypeVar
from uuid import UUID, uuid4

import orjson

log = getLogger(__name__)


class Entity:
    def __init__(
        self,
        *,
        entity_id: str,
        created_at: datetime | None,
        updated_at: datetime | None,
        version: int = 0,
    ) -> None:
        self._updated_at = updated_at or datetime.utcnow()
        self._entity_id = entity_id
        self._created_at = created_at
        self._version = version
        self._batch: list[Any] = []

    def drain(self) -> list["EntityEvent[str]"]:
        tmp = self._batch
        self._batch = []
        return tmp

    @property
    def entity_id(self) -> str:
        return self._entity_id

    @property
    def version(self) -> int:
        return self._version

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime) -> None:
        self._updated_at = value


SelfEntityEvent = TypeVar("SelfEntityEvent", bound="EntityEvent")


class EntityEvent(ABC):
    __event_class__ = "entity"
    __entity_type__ = "any"

    def __init__(
        self,
        *,
        event_created_at: datetime | None,
        published_at: datetime | None,
        entity_id: str,
        event_id: UUID | None = None,
    ) -> None:
        self._event_created_at = event_created_at or datetime.utcnow()
        self._entity_id = entity_id
        self._published_at = published_at
        self._session_uuid = None
        self.profile_int_id = None
        self._api_request_uuid = None
        self._source_dump = None
        self._event_id = event_id or uuid4()

    @property
    def event_id(self) -> UUID:
        return self._event_id

    @property
    def entity_id(self) -> str:
        return self._entity_id

    @property
    def event_created_at(self) -> datetime:
        return self._event_created_at

    @property
    def published_at(self) -> datetime | None:
        return self._published_at

    def head(self) -> dict[str, Any]:
        collector = {}
        if self._published_at is None:
            self._published_at = datetime.utcnow()

        collector["event_id"] = self._event_id
        collector["event_type"] = self.__event_class__
        collector["event_name"] = type(self).__name__
        collector["entity_id"] = self._entity_id
        collector["entity_type"] = self.__entity_type__
        collector["event_created_at"] = int(self._event_created_at.timestamp() * 1000)
        collector["published_at"] = int(self._published_at.timestamp() * 1000)
        return collector

    @abstractmethod
    def body(self) -> dict[str, Any]:
        pass

    def deserialise_body(self) -> dict[str, Any]:
        pass

    @classmethod
    def deserialise(cls, raw: bytes) -> SelfEntityEvent:
        raw_dict = orjson.loads(raw)
        head = raw_dict["head"]
        event = cls(
            event_created_at=datetime.fromtimestamp(head["event_created_at"] / 1000),
            entity_id=head["entity_id"],
            published_at=head["published_at"],
            **{
                key: datetime.fromtimestamp(value / 1000) if key.endswith("_at") else value
                for key, value in raw_dict["body"].items()
            },
        )
        event.source_dump = raw_dict
        event._event_id = head.get("event_id", uuid4())
        return event

    @property
    def source_dump(self) -> dict | None:
        return self._source_dump

    @source_dump.setter
    def source_dump(self, value: dict) -> None:
        self._source_dump = value

    def serialize(
        self,
    ) -> bytes:
        return orjson.dumps({"head": self.head(), "body": self.body()})


class Command:
    def __init__(
        self,
        *,
        principal_id: str,
        command_id: str,
        created_at: datetime | None,
    ) -> None:
        self._principal_id = principal_id
        self._command_id = command_id
        self._created_at = created_at or datetime.utcnow()

    @property
    def principal_id(self) -> str:
        return self._principal_id

    @property
    def command_id(self) -> str:
        return self._command_id

    @property
    def created_at(self) -> datetime:
        return self._created_at
