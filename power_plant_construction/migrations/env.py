from logging.config import fileConfig
import logging
import os
import sys

sys.path.insert(0, os.getcwd())

from alembic import context  # noqa: E402
from sqlalchemy import engine_from_config, pool  # noqa: E402

from power_plant_construction.db import env_to_dsn  # noqa: E402
from power_plant_construction.migrations.migrations_config import MigrationsConfig  # noqa: E402

sys.path.insert(0, os.getcwd())

log = logging.getLogger(__name__)
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

migration_config = MigrationsConfig()

config.set_main_option(
    "sqlalchemy.url",
    env_to_dsn(
        user=migration_config.DB_USER,
        password=migration_config.DB_PASSWORD,
        hosts=migration_config.DB_HOSTS,
        port=migration_config.DB_PORT,
        name=migration_config.DB_NAME,
        dialect="postgresql",
    ).replace("%", "%%"),
)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    log.info("running migration script offline")
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    log.info("running migration script online")
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),  # type: ignore
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    log.info("acquiring connection")
    with connectable.connect() as connection:
        log.info("connection acquired")
        context.configure(connection=connection, target_metadata=target_metadata)
        log.info("connection configured, starting transaction")
        with context.begin_transaction():
            log.info("starting migration")
            try:
                context.run_migrations()
            except Exception as e:
                log.info("migrations failed")
                raise e

    log.info("migrations performed")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
