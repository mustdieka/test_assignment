from typing import Mapping, Optional

from asyncpg.pool import PoolConnectionProxy

from event_sourcing.entity import EntityEvent
from power_plant_construction.entities.user import User, UserCreated


class UserRepo:
    @staticmethod
    def _record_to_user(record: Mapping | None) -> User | None:
        if not record:
            return None
        return User(
            entity_id=record["entity_id"],
            login=record["login"],
            name=record["name"],
            role=record["role"],
            password_hashed=record["password_hashed"],
            salt=record["salt"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )

    async def fetch_by_id(self, conn: PoolConnectionProxy, *, entity_id: str) -> Optional[User]:
        user_record = await conn.fetchrow(
            "select * from users where entity_id=$1",
            entity_id,
        )

        return self._record_to_user(user_record)

    async def fetch_by_login(self, conn: PoolConnectionProxy, *, login: str) -> Optional[User]:
        user_record = await conn.fetchrow(
            "select * from users where login=$1",
            login,
        )

        return self._record_to_user(user_record)

    async def persist(self, conn: PoolConnectionProxy, batch: list[EntityEvent]) -> None:
        for event in batch:
            if isinstance(event, UserCreated):
                await conn.execute(
                    """insert into users
                        (
                            entity_id,
                            login,
                            name,
                            role,
                            password_hashed,
                            salt
                        )
                        values ($1, $2, $3, $4, $5, $6)
                    """,
                    event.entity_id,
                    event.login,
                    event.name,
                    event.role,
                    event.password_hashed,
                    event.salt,
                )
            else:
                raise AssertionError()


_USER_REPO: UserRepo | None = None


def get_user_repo() -> UserRepo:
    global _USER_REPO  # pylint: disable=global-statement
    if _USER_REPO is None:
        _USER_REPO = UserRepo()

    return _USER_REPO
