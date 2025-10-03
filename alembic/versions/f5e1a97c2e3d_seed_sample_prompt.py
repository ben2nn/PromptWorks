"""seed sample prompt data

Revision ID: f5e1a97c2e3d
Revises: 0005_drop_desc_params
Create Date: 2025-10-05 18:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f5e1a97c2e3d"
down_revision: Union[str, None] = "0005_drop_desc_params"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_CLASS_NAME = "默认分类"
DEFAULT_CLASS_DESCRIPTION = "系统自动创建的默认分类"
SAMPLE_PROMPT_NAME = "示例：客服欢迎语"
SAMPLE_PROMPT_AUTHOR = "系统预置"
SAMPLE_PROMPT_DESCRIPTION = "面向客服首次接待的欢迎语示例"
SAMPLE_VERSION_NAME = "v1.0.0"
SAMPLE_VERSION_CONTENT = (
    "你是一名资深客服代表，请使用亲切、专业的语气欢迎客户。\n"
    "1. 简要自我介绍，并表明乐于协助。\n"
    "2. 询问客户关注的问题点。\n"
    "3. 告知可提供的帮助范围，并给出下一步指引。"
)


def _get_or_create_default_class(connection: sa.engine.Connection) -> int:
    class_id = connection.execute(
        sa.text("SELECT id FROM prompts_class WHERE name = :name"),
        {"name": DEFAULT_CLASS_NAME},
    ).scalar_one_or_none()
    if class_id is not None:
        return class_id

    connection.execute(
        sa.text(
            "INSERT INTO prompts_class (name, description) VALUES (:name, :description)"
        ),
        {"name": DEFAULT_CLASS_NAME, "description": DEFAULT_CLASS_DESCRIPTION},
    )
    return connection.execute(
        sa.text("SELECT id FROM prompts_class WHERE name = :name"),
        {"name": DEFAULT_CLASS_NAME},
    ).scalar_one()


def _attach_default_tags(connection: sa.engine.Connection, prompt_id: int) -> None:
    tag_ids = (
        connection.execute(
            sa.text("SELECT id FROM prompt_tags ORDER BY id ASC LIMIT 2")
        )
        .scalars()
        .all()
    )
    for tag_id in tag_ids:
        connection.execute(
            sa.text(
                "INSERT INTO prompt_tag_links (prompt_id, tag_id) VALUES (:prompt_id, :tag_id)"
            ),
            {"prompt_id": prompt_id, "tag_id": tag_id},
        )


def upgrade() -> None:
    connection = op.get_bind()

    prompt_exists = connection.execute(
        sa.text("SELECT 1 FROM prompts WHERE name = :name"),
        {"name": SAMPLE_PROMPT_NAME},
    ).scalar_one_or_none()
    if prompt_exists:
        return

    class_id = _get_or_create_default_class(connection)

    connection.execute(
        sa.text(
            "INSERT INTO prompts (class_id, name, description, author) "
            "VALUES (:class_id, :name, :description, :author)"
        ),
        {
            "class_id": class_id,
            "name": SAMPLE_PROMPT_NAME,
            "description": SAMPLE_PROMPT_DESCRIPTION,
            "author": SAMPLE_PROMPT_AUTHOR,
        },
    )

    prompt_id = connection.execute(
        sa.text("SELECT id FROM prompts WHERE class_id = :class_id AND name = :name"),
        {"class_id": class_id, "name": SAMPLE_PROMPT_NAME},
    ).scalar_one()

    connection.execute(
        sa.text(
            "INSERT INTO prompts_versions (prompt_id, version, content) "
            "VALUES (:prompt_id, :version, :content)"
        ),
        {
            "prompt_id": prompt_id,
            "version": SAMPLE_VERSION_NAME,
            "content": SAMPLE_VERSION_CONTENT,
        },
    )

    version_id = connection.execute(
        sa.text(
            "SELECT id FROM prompts_versions WHERE prompt_id = :prompt_id "
            "AND version = :version"
        ),
        {"prompt_id": prompt_id, "version": SAMPLE_VERSION_NAME},
    ).scalar_one()

    connection.execute(
        sa.text(
            "UPDATE prompts SET current_version_id = :version_id WHERE id = :prompt_id"
        ),
        {"version_id": version_id, "prompt_id": prompt_id},
    )

    _attach_default_tags(connection, prompt_id)


def downgrade() -> None:
    connection = op.get_bind()

    prompt_id = connection.execute(
        sa.text("SELECT id FROM prompts WHERE name = :name"),
        {"name": SAMPLE_PROMPT_NAME},
    ).scalar_one_or_none()
    if prompt_id is None:
        return

    connection.execute(
        sa.text("DELETE FROM prompt_tag_links WHERE prompt_id = :prompt_id"),
        {"prompt_id": prompt_id},
    )
    connection.execute(
        sa.text("DELETE FROM prompts_versions WHERE prompt_id = :prompt_id"),
        {"prompt_id": prompt_id},
    )
    connection.execute(
        sa.text("DELETE FROM prompts WHERE id = :prompt_id"),
        {"prompt_id": prompt_id},
    )

    remaining = connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM prompts "
            "WHERE class_id = (SELECT id FROM prompts_class WHERE name = :name)"
        ),
        {"name": DEFAULT_CLASS_NAME},
    ).scalar_one()
    if remaining == 0:
        connection.execute(
            sa.text("DELETE FROM prompts_class WHERE name = :name"),
            {"name": DEFAULT_CLASS_NAME},
        )
