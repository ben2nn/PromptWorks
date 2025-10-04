"""add batch id to test runs

Revision ID: 9b546f1b6f1a
Revises: 07f7c967ab21
Create Date: 2025-10-06 15:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b546f1b6f1a"
down_revision: Union[str, None] = "07f7c967ab21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "test_runs",
        sa.Column("batch_id", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_test_runs_batch_id", "test_runs", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_test_runs_batch_id", table_name="test_runs")
    op.drop_column("test_runs", "batch_id")
