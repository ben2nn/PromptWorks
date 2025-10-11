"""merge prompt test branch heads

Revision ID: 2d8d3a4e0c8b
Revises: 3152d7c2b4f0, 72f3f786c4a1
Create Date: 2025-10-11 17:05:00.000000

"""

from typing import Sequence, Union

from alembic import op  # noqa: F401 - 维持 Alembic 导入规范


revision: str = "2d8d3a4e0c8b"
down_revision: Union[str, tuple[str, ...], None] = ("3152d7c2b4f0", "72f3f786c4a1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """该迁移仅用于合并分支，不包含业务变更。"""


def downgrade() -> None:
    """回滚时无需操作。"""
