from __future__ import annotations

import pytest

from app.schemas.prompt import (
    PromptClassCreate,
    PromptClassUpdate,
    PromptCreate,
    PromptTagCreate,
    PromptTagUpdate,
    PromptUpdate,
)


def test_prompt_tag_create_normalizes_payload():
    tag = PromptTagCreate(name="  助手  ", color="#00ff00")
    assert tag.name == "助手"
    assert tag.color == "#00FF00"


def test_prompt_tag_update_validates_inputs():
    payload = PromptTagUpdate(name="  新标签  ", color="#aa11aa")
    assert payload.name == "新标签"
    assert payload.color == "#AA11AA"

    with pytest.raises(ValueError):
        PromptTagUpdate(name="   ")


def test_prompt_create_requires_class_reference():
    with pytest.raises(ValueError):
        PromptCreate(
            name="助手",
            version="v1",
            content="内容",
            class_id=None,
            class_name="  ",
        )

    payload = PromptCreate(
        name="助手",
        version="v1",
        content="内容",
        class_name="  新分类  ",
    )
    assert payload.class_name == "  新分类  "


def test_prompt_update_validates_version_and_class_name():
    with pytest.raises(ValueError):
        PromptUpdate(version="v2")

    with pytest.raises(ValueError):
        PromptUpdate(class_id=None, class_name="   ")

    payload = PromptUpdate(version="v2", content="新内容")
    assert payload.version == "v2"
    assert payload.content == "新内容"


def test_prompt_class_validations():
    created = PromptClassCreate(name="  分类  ")
    assert created.name == "分类"

    with pytest.raises(ValueError):
        PromptClassCreate(name="   ")

    with pytest.raises(ValueError):
        PromptClassUpdate(name="   ")
