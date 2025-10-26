"""add_dual_prompt_fields

Revision ID: e7e517f0f530
Revises: 95aaea879464
Create Date: 2025-10-25 19:13:37.522338

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = 'e7e517f0f530'
down_revision: Union[str, None] = '95aaea879464'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply the migration."""
    # 添加中文内容字段
    op.add_column('prompts_versions', sa.Column('contentzh', sa.Text(), nullable=True, comment='中文提示词内容'))


def downgrade() -> None:
    """Revert the migration."""
    # 删除中文内容字段
    op.drop_column('prompts_versions', 'contentzh')
