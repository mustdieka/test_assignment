from datetime import datetime
from typing import Any

from passlib.context import CryptContext

from contracts.schemas.user import UserRole
from event_sourcing.entity import Entity, EntityEvent

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCreated(EntityEvent):
    __entity_type__ = "User"

    def __init__(
        self,
        *,
        entity_id: str,
        login: str,
        name: str,
        role: UserRole,
        password_hashed: str,
        salt: str,
        event_created_at: datetime | None = None,
        published_at: datetime | None = None,
    ) -> None:
        super().__init__(event_created_at=event_created_at, published_at=published_at, entity_id=entity_id)
        self._login = login
        self._name = name
        self._role = role
        self._password_hashed = password_hashed
        self._salt = salt

    def body(self) -> dict[str, Any]:
        return {
            "login": self._login,
            "name": self._name,
            "role": self._role,
            "password_hashed": self._password_hashed,
            "salt": self._salt,
        }

    @property
    def login(self) -> str:
        return self._login

    @property
    def name(self) -> str:
        return self._name

    @property
    def role(self) -> UserRole:
        return self._role

    @property
    def password_hashed(self) -> str:
        return self._password_hashed

    @property
    def salt(self) -> str:
        return self._salt


class User(Entity):
    AGGREGATE_EVENT_TYPES = UserCreated

    def __init__(
        self,
        *,
        entity_id: str,
        login: str,
        name: str,
        role: UserRole,
        password_hashed: str,
        salt: str,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__(entity_id=entity_id, created_at=created_at, updated_at=updated_at)
        self._login = login
        self._name = name
        self._role = role
        self._password_hashed = password_hashed
        self._salt = salt

    @property
    def login(self) -> str:
        return self._login

    @property
    def name(self) -> str:
        return self._name

    @property
    def role(self) -> UserRole:
        return self._role

    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password + self._salt, self._password_hashed)

    @classmethod
    def new(
        cls,
        *,
        entity_id: str,
        login: str,
        name: str,
        role: UserRole,
        plain_password: str,
    ) -> "User":

        salt = login
        password_hashed = pwd_context.hash(plain_password + salt)
        user = User(
            entity_id=entity_id,
            login=login,
            name=name,
            role=role,
            password_hashed=password_hashed,
            salt=salt,
        )
        user._batch.append(
            UserCreated(
                entity_id=entity_id,
                login=login,
                name=name,
                role=role,
                password_hashed=password_hashed,
                salt=salt,
            )
        )

        return user
