"""init db

Revision ID: 22041f5b4af7

"""
from alembic import op
from sqlalchemy import Column, DateTime, Enum, String, text

# revision identifiers, used by Alembic.
revision = "22041f5b4af7"
down_revision = None
branch_labels = None
depends_on = None

UTC_NOW_FN = text("(now() at time zone 'utc')")


def upgrade() -> None:

    op.create_table(
        "users",
        Column("entity_id", String, primary_key=True),
        Column("login", String, nullable=False, unique=True),
        Column("name", String, nullable=False),
        Column("role", Enum("WORKER", "MANAGER", name="user_role_enum"), nullable=False),
        Column("password_hashed", String, nullable=False),
        Column("salt", String, nullable=False),
        Column("created_at", DateTime, server_default=UTC_NOW_FN, nullable=False),
        Column("updated_at", DateTime, server_default=UTC_NOW_FN, nullable=False),
    )

    op.create_table(
        "tasks",
        Column("entity_id", String, primary_key=True),
        Column("title", String, nullable=False),
        Column("description", String, nullable=False),
        Column("author", String, nullable=False),
        Column("assignee", String, nullable=False),
        Column(
            "status",
            Enum("PENDING", "IN_PROGRESS", "COMPLETED", name="task_status_enum"),
            nullable=False,
        ),
        Column("created_at", DateTime, server_default=UTC_NOW_FN, nullable=False),
        Column("updated_at", DateTime, server_default=UTC_NOW_FN, nullable=False),
    )

    op.create_table(
        "task_dependencies",
        Column("entity_id", String, primary_key=True),
        Column("depends_on", String, primary_key=True),
        Column("created_at", DateTime, server_default=UTC_NOW_FN, nullable=False),
        Column("updated_at", DateTime, server_default=UTC_NOW_FN, nullable=False),
    )

    op.create_table(
        "notifications",
        Column("entity_id", String, primary_key=True),
        Column("title", String, nullable=False),
        Column("content", String, nullable=False),
        Column(
            "status",
            Enum("UNREAD", "READ", name="notification_status_enum"),
            nullable=False,
        ),
        Column("receiver", String, nullable=False),
        Column("created_at", DateTime, server_default=UTC_NOW_FN, nullable=False),
        Column("updated_at", DateTime, server_default=UTC_NOW_FN, nullable=False),
    )


def downgrade() -> None:
    CREATED_TABLES = (
        "users",
        "tasks",
        "dependencies",
        "notifications",
    )
    for table in CREATED_TABLES:
        op.execute(f"drop table {table} cascade")

    CREATED_ENUMS = (
        "user_role_enum",
        "task_status_enum",
        "notification_status_enum",
    )
    for enum_type in CREATED_ENUMS:
        Enum(name=enum_type).drop(op.get_bind(), checkfirst=False)
