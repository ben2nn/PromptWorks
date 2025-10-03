"""seed default prompt tags

Revision ID: efea0d0224c5
Revises: ddc6143e8fb8
Create Date: 2025-10-03 13:58:18.007775

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "efea0d0224c5"
down_revision: Union[str, None] = "ddc6143e8fb8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_TAGS = [
    {"name": "通用运营", "color": "#409EFF"},
    {"name": "客户关怀", "color": "#67C23A"},
    {"name": "营销活动", "color": "#F56C6C"},
    {"name": "产品公告", "color": "#E6A23C"},
    {"name": "数据分析", "color": "#909399"},
]


def upgrade() -> None:
    """插入五个常用标签作为默认数据。"""

    connection = op.get_bind()
    for tag in DEFAULT_TAGS:
        existing_id = connection.execute(
            sa.text("SELECT id FROM prompt_tags WHERE name = :name"),
            {"name": tag["name"]},
        ).scalar_one_or_none()

        if existing_id is not None:
            continue

        connection.execute(
            sa.text("INSERT INTO prompt_tags (name, color) VALUES (:name, :color)"),
            tag,
        )


def downgrade() -> None:
    """在无引用的情况下移除默认标签。"""

    connection = op.get_bind()
    for tag in DEFAULT_TAGS:
        tag_id = connection.execute(
            sa.text("SELECT id FROM prompt_tags WHERE name = :name"),
            {"name": tag["name"]},
        ).scalar_one_or_none()

        if tag_id is None:
            continue

        usage = connection.execute(
            sa.text("SELECT COUNT(*) FROM prompt_tag_links WHERE tag_id = :tag_id"),
            {"tag_id": tag_id},
        ).scalar_one()

        if usage:
            continue

        connection.execute(
            sa.text("DELETE FROM prompt_tags WHERE id = :tag_id"),
            {"tag_id": tag_id},
        )
