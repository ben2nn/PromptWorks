"""add prompt tags support

Revision ID: 0003_prompt_tags
Revises: 0002_prompt_class_and_versions
Create Date: 2025-09-20 00:30:00

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_prompt_tags"
down_revision: Union[str, None] = "0002_prompt_class_and_versions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TAG_SEED_DATA: list[tuple[str, str]] = [
    ("常规", "#2563EB"),
    ("测试", "#10B981"),
    ("紧急", "#F97316"),
    ("实验", "#8B5CF6"),
    ("归档", "#6B7280"),
]


def upgrade() -> None:
    op.create_table(
        "prompt_tags",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "prompt_tag_links",
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["prompt_id"],
            ["prompts.id"],
            ondelete="CASCADE",
            name="prompt_tag_links_prompt_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["prompt_tags.id"],
            ondelete="CASCADE",
            name="prompt_tag_links_tag_id_fkey",
        ),
        sa.PrimaryKeyConstraint("prompt_id", "tag_id"),
    )

    tags_table = sa.table(
        "prompt_tags",
        sa.column("name", sa.String(length=100)),
        sa.column("color", sa.String(length=7)),
    )
    op.bulk_insert(
        tags_table,
        [{"name": name, "color": color} for name, color in TAG_SEED_DATA],
    )


def downgrade() -> None:
    op.drop_table("prompt_tag_links")
    op.drop_table("prompt_tags")
