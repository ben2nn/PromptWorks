"""make prompt_id nullable in attachments

Revision ID: f1a2b3c4d5e6
Revises: e7e517f0f530
Create Date: 2025-10-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'e7e517f0f530'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """将 prompt_attachments 表的 prompt_id 字段改为可空，支持临时上传"""
    # 修改 prompt_id 字段为可空
    op.alter_column(
        'prompt_attachments',
        'prompt_id',
        existing_type=sa.Integer(),
        nullable=True,
        existing_nullable=False
    )


def downgrade() -> None:
    """回滚：将 prompt_id 字段改回不可空"""
    # 注意：回滚前需要确保没有 prompt_id 为 NULL 的记录
    # 否则会失败
    op.alter_column(
        'prompt_attachments',
        'prompt_id',
        existing_type=sa.Integer(),
        nullable=False,
        existing_nullable=True
    )
