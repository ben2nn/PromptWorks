"""merge_multiple_heads

Revision ID: 95aaea879464
Revises: a6b7c8d9e0f1, a1b2c3d4e5f6
Create Date: 2025-10-25 17:59:35.499789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = '95aaea879464'
down_revision: Union[str, None] = ('a6b7c8d9e0f1', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply the migration."""

    pass


def downgrade() -> None:
    """Revert the migration."""

    pass
