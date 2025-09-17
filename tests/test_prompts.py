from fastapi.testclient import TestClient


def test_create_and_list_prompts(client: TestClient):
    payload = {
        "name": "订单确认",
        "version": "v1",
        "content": "请根据输入生成订单确认邮件。",
        "description": "默认中文邮件模板",
        "author": "tester",
    }
    response = client.post("/api/v1/prompts/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["version"] == payload["version"]

    list_resp = client.get("/api/v1/prompts/")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["name"] == payload["name"]


def test_update_and_delete_prompt(client: TestClient):
    create_resp = client.post(
        "/api/v1/prompts/",
        json={
            "name": "调试提示",
            "version": "v1",
            "content": "原始内容",
        },
    )
    prompt_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        json={
            "content": "更新后的内容",
            "version": "v2",
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["content"] == "更新后的内容"
    assert updated["version"] == "v2"

    delete_resp = client.delete(f"/api/v1/prompts/{prompt_id}")
    assert delete_resp.status_code == 204

    not_found_resp = client.get(f"/api/v1/prompts/{prompt_id}")
    assert not_found_resp.status_code == 404
