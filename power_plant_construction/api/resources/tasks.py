from uuid import uuid4

from asyncpg import Pool
from fastapi import APIRouter, Body, Depends, Path, Query

from contracts.schemas.task import TaskCreateDto, TaskDependencyUpdateDto, TaskDto, TaskUpdateStatusDto
from event_sourcing.event_store_client import EventStoreClient
from power_plant_construction.api.auth import MANAGER_AUTH, MINIMAL_AUTH, LoggedInUser
from power_plant_construction.commands.task.add_dependency import AddDependency
from power_plant_construction.commands.task.create import Create
from power_plant_construction.commands.task.remove_dependency import RemoveDependency
from power_plant_construction.commands.task.update_status import UpdateStatus
from power_plant_construction.db import get_db_pool
from power_plant_construction.event_store import get_event_store
from power_plant_construction.repositories.task import TaskRepo, get_task_repo

router = APIRouter()


@router.get(
    "/",
    response_model=list[TaskDto],
)
async def get_tasks(
    only_unblocked_pending: bool = Query(False),
    pool: Pool = Depends(get_db_pool),
    task_repo: TaskRepo = Depends(get_task_repo),
    logged_in_user: LoggedInUser = Depends(MINIMAL_AUTH),
) -> list[TaskDto]:
    async with pool.acquire() as conn:
        if only_unblocked_pending:
            tasks = await task_repo.fetch_pending_unblocked_tasks(conn, assignee=logged_in_user.user)
        else:
            tasks = await task_repo.fetch_by_assignee(conn, assignee=logged_in_user.user)

        return [
            TaskDto(
                id=task.entity_id,
                title=task.title,
                description=task.description,
                status=task.status,
                author=task.author,
                assignee=task.assignee,
                depends_on=list(task.depends_on),
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
            for task in tasks
        ]


@router.post(
    "/",
    status_code=201,
)
async def create_new_task(
    task: TaskCreateDto = Body(...),
    pool: Pool = Depends(get_db_pool),
    task_repo: TaskRepo = Depends(get_task_repo),
    event_store: EventStoreClient = Depends(get_event_store),
    logged_in_user: LoggedInUser = Depends(MANAGER_AUTH),
) -> str:
    create_task_command = Create(
        command_id=str(uuid4()),
        principal_id=str(uuid4()),
        title=task.title,
        description=task.description,
        assignee=task.assignee,
        author=logged_in_user.user,
    )

    await create_task_command.execute(
        pool=pool,
        event_store=event_store,
        task_repo=task_repo,
    )

    return str(uuid4())


@router.post(
    "/{task}",
    status_code=201,
)
async def create_task(
    task: str = Path(...),
    new_status: TaskUpdateStatusDto = Body(...),
    pool: Pool = Depends(get_db_pool),
    task_repo: TaskRepo = Depends(get_task_repo),
    event_store: EventStoreClient = Depends(get_event_store),
    logged_in_user: LoggedInUser = Depends(MINIMAL_AUTH),
) -> None:
    update_status = UpdateStatus(
        command_id=str(uuid4()), principal_id=task, status=new_status.status, submitted_by=logged_in_user.user
    )

    await update_status.execute(
        pool=pool,
        event_store=event_store,
        task_repo=task_repo,
    )


@router.patch(
    "/{task}/dependencies",
    status_code=201,
)
async def update_task_dependencies(
    task: str = Path(...),
    dependency_update: TaskDependencyUpdateDto = Body(...),
    pool: Pool = Depends(get_db_pool),
    task_repo: TaskRepo = Depends(get_task_repo),
    event_store: EventStoreClient = Depends(get_event_store),
    logged_in_user: LoggedInUser = Depends(MANAGER_AUTH),
) -> None:

    for task in dependency_update.add:
        add = AddDependency(
            command_id=str(uuid4()),
            principal_id=task,
            task=task,
        )

        await add.execute(
            pool=pool,
            event_store=event_store,
            task_repo=task_repo,
        )

    for task in dependency_update.remove:
        remove = RemoveDependency(
            command_id=str(uuid4()),
            principal_id=task,
            task=task,
        )

        await remove.execute(
            pool=pool,
            event_store=event_store,
            task_repo=task_repo,
        )
