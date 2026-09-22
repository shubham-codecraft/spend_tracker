"""Add email OTP challenges.

Revision ID: 20260922_otp_challenges
Revises: 20260922_user_scoping
Create Date: 2026-09-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260922_otp_challenges"
down_revision: Union[str, Sequence[str], None] = "20260922_user_scoping"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "otp_challenges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_otp_challenges_id", "otp_challenges", ["id"], unique=False)
    op.create_index("ix_otp_challenges_email", "otp_challenges", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_otp_challenges_email", table_name="otp_challenges")
    op.drop_index("ix_otp_challenges_id", table_name="otp_challenges")
    op.drop_table("otp_challenges")