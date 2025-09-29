from datetime import datetime, timedelta, timezone

import pytest

from app.models.prompt import Prompt, PromptClass


@pytest.fixture()
def prompt_classes(db_session):
    """预置两个分类供列表与删除场景使用"""

    cls_a = PromptClass(name="分类A", description="示例A")
    cls_b = PromptClass(name="分类B", description=None)
    db_session.add_all([cls_a, cls_b])
    db_session.commit()
    return cls_a, cls_b


def test_list_prompt_classes_returns_statistics(client, db_session, prompt_classes):
    cls_a, cls_b = prompt_classes
    now = datetime.now(timezone.utc).replace(microsecond=0)
    earlier = now - timedelta(days=1)

    prompt_one = Prompt(
        name="提示一", prompt_class=cls_a, created_at=earlier, updated_at=earlier
    )
    prompt_two = Prompt(
        name="提示二", prompt_class=cls_a, created_at=now, updated_at=now
    )
    db_session.add_all([prompt_one, prompt_two])
    db_session.commit()

    response = client.get("/api/v1/prompt-classes/")
    assert response.status_code == 200
    items = response.json()
    assert [item["name"] for item in items] == ["分类A", "分类B"]

    first = items[0]
    assert first["prompt_count"] == 2
    assert first["description"] == "示例A"
    latest = datetime.fromisoformat(first["latest_prompt_updated_at"])
    assert latest == now.replace(tzinfo=None)

    second = items[1]
    assert second["prompt_count"] == 0
    assert second["latest_prompt_updated_at"] is None


def test_list_prompt_classes_supports_keyword_filter(
    client, db_session, prompt_classes
):
    response = client.get("/api/v1/prompt-classes/", params={"q": "B"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["name"] == "分类B"


def test_create_prompt_class_and_conflict(client):
    payload = {"name": "新分类", "description": "说明"}
    create_resp = client.post("/api/v1/prompt-classes/", json=payload)
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]

    conflict_resp = client.post(
        "/api/v1/prompt-classes/", json={"name": "新分类", "description": "重复"}
    )
    assert conflict_resp.status_code == 400


def test_update_prompt_class_success(client, prompt_classes):
    cls_a, _ = prompt_classes
    update_resp = client.patch(
        f"/api/v1/prompt-classes/{cls_a.id}",
        json={"name": "分类A-更新", "description": "更新后的描述"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["name"] == "分类A-更新"
    assert updated["description"] == "更新后的描述"


def test_update_prompt_class_conflict(client, prompt_classes):
    cls_a, cls_b = prompt_classes
    conflict_resp = client.patch(
        f"/api/v1/prompt-classes/{cls_b.id}", json={"name": "分类A"}
    )
    assert conflict_resp.status_code == 400


def test_update_prompt_class_not_found(client):
    resp = client.patch("/api/v1/prompt-classes/999", json={"name": "不存在"})
    assert resp.status_code == 404


def test_delete_prompt_class_blocked_by_prompts(client, db_session, prompt_classes):
    cls_a, _ = prompt_classes
    prompt = Prompt(name="阻塞用", prompt_class=cls_a)
    db_session.add(prompt)
    db_session.commit()

    delete_resp = client.delete(f"/api/v1/prompt-classes/{cls_a.id}")
    assert delete_resp.status_code == 409


def test_delete_prompt_class_success(client, prompt_classes):
    _, cls_b = prompt_classes
    delete_resp = client.delete(f"/api/v1/prompt-classes/{cls_b.id}")
    assert delete_resp.status_code == 204

    confirm_resp = client.get("/api/v1/prompt-classes/")
    names = [item["name"] for item in confirm_resp.json()]
    assert "分类B" not in names
