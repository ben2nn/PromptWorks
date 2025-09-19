from fastapi.testclient import TestClient


def test_create_and_list_prompts(client: TestClient):
    """验证创建 Prompt 后能在列表中查询且包含分类与版本信息。"""
    payload = {
        "name": "订单确认",
        "version": "v1",
        "content": "请根据输入生成客户确认邮件。",
        "description": "默认中文邮件模板",
        "author": "tester",
        "class_name": "通知类",
    }
    response = client.post("/api/v1/prompts/", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == payload["name"]
    assert data["prompt_class"]["name"] == payload["class_name"]
    assert data["current_version"]["version"] == payload["version"]
    assert data["current_version"]["content"] == payload["content"]
    assert len(data["versions"]) == 1

    list_resp = client.get("/api/v1/prompts/")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["name"] == payload["name"]
    assert items[0]["prompt_class"]["name"] == payload["class_name"]
    assert items[0]["current_version"]["version"] == payload["version"]


def test_update_and_delete_prompt(client: TestClient):
    """验证 Prompt 更新时创建新版本，删除后无法再访问。"""
    create_resp = client.post(
        "/api/v1/prompts/",
        json={
            "name": "调试提示",
            "version": "v1",
            "content": "原始内容",
            "class_name": "实验类",
        },
    )
    assert create_resp.status_code == 201
    prompt = create_resp.json()
    prompt_id = prompt["id"]

    update_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        json={
            "content": "更新后的内容",
            "version": "v2",
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["current_version"]["content"] == "更新后的内容"
    assert updated["current_version"]["version"] == "v2"
    assert len(updated["versions"]) == 2

    delete_resp = client.delete(f"/api/v1/prompts/{prompt_id}")
    assert delete_resp.status_code == 204

    not_found_resp = client.get(f"/api/v1/prompts/{prompt_id}")
    assert not_found_resp.status_code == 404
