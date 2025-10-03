"""drop description and model parameters

Revision ID: 0005_drop_desc_params
Revises: 0004_refactor_llm_providers
Create Date: 2025-10-05 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_drop_desc_params"
down_revision: Union[str, None] = "0004_refactor_llm_providers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("llm_providers", "description")
    op.drop_column("llm_models", "parameters")


def downgrade() -> None:
    op.add_column(
        "llm_models",
        sa.Column(
            "parameters",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    op.add_column(
        "llm_providers",
        sa.Column("description", sa.Text(), nullable=True),
    )
