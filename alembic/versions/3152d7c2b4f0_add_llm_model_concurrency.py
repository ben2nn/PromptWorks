"""add concurrency limit to llm models

Revision ID: 3152d7c2b4f0
Revises: 9b546f1b6f1a
Create Date: 2025-10-06 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3152d7c2b4f0"
down_revision: Union[str, None] = "9b546f1b6f1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "llm_models",
        sa.Column(
            "concurrency_limit",
            sa.Integer(),
            nullable=False,
            server_default="5",
        ),
    )


def downgrade() -> None:
    op.drop_column("llm_models", "concurrency_limit")
