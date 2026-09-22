"""Add user ownership to expenses and remove client credentials.

Revision ID: 20260922_user_scoping
Revises:
Create Date: 2026-09-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260922_user_scoping"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def _create_expenses_table() -> None:
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_expenses_id", "expenses", ["id"], unique=False)
    op.create_index("ix_expenses_user_id", "expenses", ["user_id"], unique=False)
    op.create_index("ix_expenses_category", "expenses", ["category"], unique=False)
    op.create_index("ix_expenses_date", "expenses", ["date"], unique=False)
    op.create_index("ix_expenses_category_date", "expenses", ["category", "date"], unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "users" not in tables:
        _create_users_table()
        inspector = inspect(bind)

    if "expenses" not in tables:
        _create_expenses_table()
    else:
        expense_columns = {column["name"] for column in inspector.get_columns("expenses")}
        if "user_id" not in expense_columns:
            op.add_column("expenses", sa.Column("user_id", sa.Integer(), nullable=True))

        user_columns = {column["name"] for column in inspector.get_columns("users")}
        user_count = bind.execute(sa.text("SELECT COUNT(*) FROM users")).scalar_one()
        if user_count == 0:
            if "client_id" in user_columns:
                bind.execute(
                    sa.text(
                        "INSERT INTO users "
                        "(email, first_name, last_name, client_id) "
                        "VALUES (:email, :first_name, :last_name, :client_id)"
                    ),
                    {
                        "email": "legacy@spend-tracker.invalid",
                        "first_name": "Legacy",
                        "last_name": "User",
                        "client_id": "legacy-migration",
                    },
                )
            else:
                bind.execute(
                    sa.text(
                        "INSERT INTO users (email, first_name, last_name) "
                        "VALUES (:email, :first_name, :last_name)"
                    ),
                    {
                        "email": "legacy@spend-tracker.invalid",
                        "first_name": "Legacy",
                        "last_name": "User",
                    },
                )

        legacy_user_id = bind.execute(
            sa.text("SELECT id FROM users ORDER BY id LIMIT 1")
        ).scalar_one()
        bind.execute(
            sa.text("UPDATE expenses SET user_id = :user_id WHERE user_id IS NULL"),
            {"user_id": legacy_user_id},
        )
        op.alter_column("expenses", "user_id", nullable=False)
        expense_indexes = {index["name"] for index in inspector.get_indexes("expenses")}
        if "ix_expenses_user_id" not in expense_indexes:
            op.create_index("ix_expenses_user_id", "expenses", ["user_id"], unique=False)
        foreign_keys = {foreign_key.get("name") for foreign_key in inspector.get_foreign_keys("expenses")}
        if "fk_expenses_user_id_users" not in foreign_keys:
            op.create_foreign_key(
                "fk_expenses_user_id_users",
                "expenses",
                "users",
                ["user_id"],
                ["id"],
            )

    inspector = inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "client_id" in user_columns:
        user_indexes = {index["name"] for index in inspector.get_indexes("users")}
        if "ix_users_client_id" in user_indexes:
            op.drop_index("ix_users_client_id", table_name="users")
        op.drop_column("users", "client_id")


def downgrade() -> None:
    raise RuntimeError("This migration is intentionally irreversible because legacy expenses cannot be safely unassigned.")
