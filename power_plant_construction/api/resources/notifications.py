from uuid import uuid4

from asyncpg import Pool
from fastapi import APIRouter, Depends, Path

from contracts.schemas.notification import NotificationDto
from event_sourcing.event_store_client import EventStoreClient
from power_plant_construction.api.auth import MINIMAL_AUTH, LoggedInUser
from power_plant_construction.commands.notification.mark_read import MarkRead
from power_plant_construction.db import get_db_pool
from power_plant_construction.event_store import get_event_store
from power_plant_construction.repositories.notification import NotificationRepo, get_notification_repo

router = APIRouter()


@router.get(
    "/",
    response_model=list[NotificationDto],
)
async def get_notifications_list(
    pool: Pool = Depends(get_db_pool),
    notification_repo: NotificationRepo = Depends(get_notification_repo),
    logged_in_user: LoggedInUser = Depends(MINIMAL_AUTH),
) -> list[NotificationDto]:
    async with pool.acquire() as conn:
        notifications = await notification_repo.fetch_all_for_receiver(conn, receiver=logged_in_user.user)
        return [
            NotificationDto(
                id=notification.entity_id,
                title=notification.title,
                content=notification.content,
                status=notification.status,
                created_at=notification.created_at,
                updated_at=notification.updated_at,
            )
            for notification in notifications
        ]


@router.post(
    "/{notification}/read",
    status_code=200,
)
async def set_notification_as_read(
    notification: str = Path(...),
    pool: Pool = Depends(get_db_pool),
    notification_repo: NotificationRepo = Depends(get_notification_repo),
    event_store: EventStoreClient = Depends(get_event_store),
    logged_in_user: LoggedInUser = Depends(MINIMAL_AUTH),
) -> None:
    update_knowledge_items_command = MarkRead(
        command_id=str(uuid4()), principal_id=notification, receiver=logged_in_user.user
    )

    await update_knowledge_items_command.execute(
        pool=pool, event_store=event_store, notification_repo=notification_repo
    )
