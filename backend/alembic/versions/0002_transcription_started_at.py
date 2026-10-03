"""add transcription started_at

Revision ID: 0002_started_at
Revises: b435e14d74c1
Create Date: 2026-10-03 15:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_started_at"
down_revision: str | None = "b435e14d74c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transcriptions", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("transcriptions", "started_at")
