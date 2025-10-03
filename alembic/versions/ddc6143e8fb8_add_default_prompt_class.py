"""add default prompt class

Revision ID: ddc6143e8fb8
Revises: 0003_prompt_tags
Create Date: 2025-10-03 13:50:27.116107

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ddc6143e8fb8"
down_revision: Union[str, None] = "0003_prompt_tags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_CLASS_NAME = "默认分类"
DEFAULT_CLASS_DESCRIPTION = "系统自动创建的默认分类"


def upgrade() -> None:
    """确保数据库中存在默认 Prompt 分类。"""

    connection = op.get_bind()
    existing_id = connection.execute(
        sa.text("SELECT id FROM prompts_class WHERE name = :name"),
        {"name": DEFAULT_CLASS_NAME},
    ).scalar_one_or_none()

    if existing_id is not None:
        return

    connection.execute(
        sa.text(
            "INSERT INTO prompts_class (name, description) VALUES (:name, :description)"
        ),
        {"name": DEFAULT_CLASS_NAME, "description": DEFAULT_CLASS_DESCRIPTION},
    )


def downgrade() -> None:
    """在安全的前提下移除默认 Prompt 分类。"""

    connection = op.get_bind()
    default_id = connection.execute(
        sa.text("SELECT id FROM prompts_class WHERE name = :name"),
        {"name": DEFAULT_CLASS_NAME},
    ).scalar_one_or_none()

    if default_id is None:
        return

    prompt_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM prompts WHERE class_id = :class_id"),
        {"class_id": default_id},
    ).scalar_one()

    if prompt_count:
        return

    connection.execute(
        sa.text("DELETE FROM prompts_class WHERE id = :class_id"),
        {"class_id": default_id},
    )
