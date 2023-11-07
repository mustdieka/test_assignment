import asyncio
import logging
import os

from click import Context as ClickContext
import click

logging.basicConfig()

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@click.group()
def cli():
    pass


@cli.command("start-api")
def start_api():
    log.info("Starting the api")
    from power_plant_construction.api.api_config import ApiConfig

    config = ApiConfig()
    address = ("--host", config.API_HOST, "--port", config.API_PORT)
    autoreload = ()
    autoreload = ("--reload",)

    if os.name == "nt":
        args = [
            "python",
            "-m",
            "uvicorn",
            *address,
            *autoreload,
            "--factory",
            '"power_plant_construction.api:create_api"',
        ]

    else:
        address = f"--bind={config.API_HOST}:{config.API_PORT}"
        args = [
            "python",
            "-u",
            "-P",
            "-m",
            "gunicorn",
            "power_plant_construction.api:create_api()",
            address,
            "-k",
            "uvicorn.workers.UvicornWorker",
            "--access-logfile=-",
            *autoreload,
        ]

    os.execvpe("python", [str(v) for v in args], os.environ)


@cli.command("start-app")
def start_app():
    log.info("Starting the app")
    from power_plant_construction.app.run import run_app

    asyncio.run(run_app())


@cli.command("db-migrate")
def db_migrate():
    """Migrates Database to the latest Schema"""
    log.info("Starting the migrations")
    args = ["python", "-u", "-P", "-m", "alembic", "upgrade", "head"]

    os.execvpe("python", [str(v) for v in args], os.environ)


async def init_hometask_cli() -> None:
    from asyncpg import create_pool as create_db_pool

    from contracts.schemas.user import UserRole
    from event_sourcing.event_store_client import EventStoreClient
    from power_plant_construction.app.app_config import get_app_config
    from power_plant_construction.db import env_to_dsn
    from power_plant_construction.entities.task import TaskCreated, TaskDependencyAdded, TaskStatus
    from power_plant_construction.entities.user import User
    from power_plant_construction.repositories.task import get_task_repo
    from power_plant_construction.repositories.user import get_user_repo

    app_config = get_app_config()

    db_dsn = env_to_dsn(
        user=app_config.DB_USER,
        password=app_config.DB_PASSWORD,
        hosts=app_config.DB_HOSTS,
        port=app_config.DB_PORT,
        name=app_config.DB_NAME,
    )

    event_store = EventStoreClient(
        nats_dsn=app_config.NATS_DSN,
        event_types=set(),
    )
    log.info("Setting up db connection pool")
    db_pool = await create_db_pool(db_dsn, max_size=30)
    await event_store.connect()
    user_repo = get_user_repo()
    task_repo = get_task_repo()
    async with db_pool.acquire() as conn:
        manager = await user_repo.fetch_by_id(conn, entity_id="0")
        if manager:
            return

        manager = User.new(
            entity_id="u0",
            login="manager",
            name="Richard",
            role=UserRole.MANAGER,
            plain_password="manager",
        )

        worker = User.new(
            entity_id="u1",
            login="worker",
            name="Nathan",
            role=UserRole.WORKER,
            plain_password="worker",
        )
        user_batch = manager.drain()
        user_batch.extend(worker.drain())
        await user_repo.persist(conn, user_batch)
        await event_store.publish_batch(user_batch)

        task_batch = [
            TaskCreated(
                entity_id=f"t{t}",
                title=f"T{t}",
                description=f"some description of task T{t}",
                status=TaskStatus.PENDING,
                assignee="u1",
                author="u0",
            )
            for t in range(10)
        ]

        task_batch.extend(
            (
                TaskDependencyAdded(entity_id="t5", depends_on="t2"),
                TaskDependencyAdded(entity_id="t5", depends_on="t4"),
                TaskDependencyAdded(entity_id="t3", depends_on="t1"),
                TaskDependencyAdded(entity_id="t3", depends_on="t2"),
                TaskDependencyAdded(entity_id="t4", depends_on="t3"),
                TaskDependencyAdded(entity_id="t9", depends_on="t8"),
                TaskDependencyAdded(entity_id="t7", depends_on="t2"),
                TaskDependencyAdded(entity_id="t6", depends_on="t1"),
            )
        )

        await task_repo.persist(conn, task_batch)
        await event_store.publish_batch(task_batch)


@cli.command("init-hometask")
@click.pass_context
def init_hometask(ctx: ClickContext):
    import asyncio

    asyncio.run(init_hometask_cli())


if __name__ == "__main__":
    os.environ.setdefault("ENV_PATH", ".env")
    os.environ["PYTHONPATH"] = "."
    cli()
