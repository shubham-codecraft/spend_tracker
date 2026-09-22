"""Remove unused OTP challenge storage.

Revision ID: 20260923_remove_otp_challenges
Revises: 20260922_otp_challenges
Create Date: 2026-09-23
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260923_remove_otp_challenges"
down_revision: Union[str, Sequence[str], None] = "20260922_otp_challenges"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_otp_challenges_email", table_name="otp_challenges")
    op.drop_index("ix_otp_challenges_id", table_name="otp_challenges")
    op.drop_table("otp_challenges")


def downgrade() -> None:
    raise RuntimeError("OTP challenge storage was removed and cannot be restored automatically.")
