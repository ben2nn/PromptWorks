"""add media type and attachments

Revision ID: a6b7c8d9e0f1
Revises: f5e1a97c2e3d
Create Date: 2024-10-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a6b7c8d9e0f1'
down_revision: Union[str, None] = 'f5e1a97c2e3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建媒体类型枚举
    media_type_enum = postgresql.ENUM(
        'text', 'image', 'document', 'audio', 'video',
        name='mediatype'
    )
    media_type_enum.create(op.get_bind())
    
    # 添加媒体类型字段�?prompts �?
    op.add_column('prompts', sa.Column('media_type', media_type_enum, nullable=False, server_default='text'))
    op.create_index('idx_prompts_media_type', 'prompts', ['media_type'])
    
    # 创建附件�?
    op.create_table('prompt_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prompt_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('file_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_prompt_attachments_prompt_id', 'prompt_attachments', ['prompt_id'])
    op.create_index('idx_prompt_attachments_mime_type', 'prompt_attachments', ['mime_type'])


def downgrade() -> None:
    # 删除附件表和索引
    op.drop_index('idx_prompt_attachments_mime_type', table_name='prompt_attachments')
    op.drop_index('idx_prompt_attachments_prompt_id', table_name='prompt_attachments')
    op.drop_table('prompt_attachments')
    
    # 删除 prompts 表的媒体类型字段和索�?
    op.drop_index('idx_prompts_media_type', table_name='prompts')
    op.drop_column('prompts', 'media_type')
    
    # 删除媒体类型枚举
    media_type_enum = postgresql.ENUM(name='mediatype')
    media_type_enum.drop(op.get_bind())
