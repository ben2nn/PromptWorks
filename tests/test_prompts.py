from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.prompt import PromptTag


def test_create_and_list_prompts(client: TestClient, db_session: Session):
    """验证创建 Prompt 时可绑定标签，并在列表与详情接口中返回。"""
    tag_notice = PromptTag(name="通知", color="#1D4ED8")
    tag_email = PromptTag(name="邮件", color="#F97316")
    db_session.add_all([tag_notice, tag_email])
    db_session.commit()

    payload = {
        "name": "订单确认",
        "version": "v1",
        "content": "请基于输入生成客户确认邮件。",
        "description": "默认中文邮件模版",
        "author": "tester",
        "class_name": "通知类",
        "tag_ids": [tag_notice.id, tag_email.id],
    }
    response = client.post("/api/v1/prompts/", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == payload["name"]
    assert data["prompt_class"]["name"] == payload["class_name"]
    assert data["current_version"]["version"] == payload["version"]
    assert data["current_version"]["content"] == payload["content"]
    assert len(data["versions"]) == 1
    assert [tag["id"] for tag in data["tags"]] == payload["tag_ids"]

    list_resp = client.get("/api/v1/prompts/")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["name"] == payload["name"]
    assert items[0]["prompt_class"]["name"] == payload["class_name"]
    assert items[0]["current_version"]["version"] == payload["version"]
    assert [tag["id"] for tag in items[0]["tags"]] == payload["tag_ids"]

    tag_list_resp = client.get("/api/v1/prompt-tags/")
    assert tag_list_resp.status_code == 200
    tag_list = tag_list_resp.json()
    assert {tag["name"] for tag in tag_list} >= {"通知", "邮件"}


def test_update_and_delete_prompt(client: TestClient, db_session: Session):
    """验证 Prompt 更新时可切换标签，删除后无法再访问。"""
    tag_initial = PromptTag(name="流程校验", color="#10B981")
    tag_new = PromptTag(name="归档", color="#6B7280")
    db_session.add_all([tag_initial, tag_new])
    db_session.commit()

    create_resp = client.post(
        "/api/v1/prompts/",
        json={
            "name": "测试提示",
            "version": "v1",
            "content": "原始内容",
            "class_name": "实验类",
            "tag_ids": [tag_initial.id],
        },
    )
    assert create_resp.status_code == 201
    prompt = create_resp.json()
    prompt_id = prompt["id"]
    assert [tag["id"] for tag in prompt["tags"]] == [tag_initial.id]

    update_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        json={
            "content": "更新后的内容",
            "version": "v2",
            "tag_ids": [tag_new.id],
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["current_version"]["content"] == "更新后的内容"
    assert updated["current_version"]["version"] == "v2"
    assert len(updated["versions"]) == 2
    assert [tag["id"] for tag in updated["tags"]] == [tag_new.id]

    clear_tags_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        json={"tag_ids": []},
    )
    assert clear_tags_resp.status_code == 200
    assert clear_tags_resp.json()["tags"] == []

    delete_resp = client.delete(f"/api/v1/prompts/{prompt_id}")
    assert delete_resp.status_code == 204

    not_found_resp = client.get(f"/api/v1/prompts/{prompt_id}")
    assert not_found_resp.status_code == 404
