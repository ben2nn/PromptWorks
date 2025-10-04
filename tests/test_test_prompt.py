from fastapi.testclient import TestClient


def _create_prompt(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/prompts/",
        json={
            "name": "对话助手",
            "version": "v1",
            "content": "你是一位擅长助人的智能助手。",
            "class_name": "聊天类",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_test_prompt_requires_prompt_version(client: TestClient):
    """缺少有效 Prompt 版本时创建测试任务返回 404。"""
    response = client.post(
        "/api/v1/test_prompt/",
        json={
            "prompt_version_id": 999,
            "model_name": "gpt-4o",
            "temperature": 0.1,
            "top_p": 0.9,
            "repetitions": 1,
        },
    )
    assert response.status_code == 404


def test_create_and_retrieve_test_prompt(client: TestClient):
    """验证测试任务创建后可通过列表和详情接口读取。"""
    prompt_payload = _create_prompt(client)
    prompt_version_id = prompt_payload["current_version"]["id"]

    create_resp = client.post(
        "/api/v1/test_prompt/",
        json={
            "prompt_version_id": prompt_version_id,
            "model_name": "gpt-4o",
            "model_version": "2024-05-01",
            "temperature": 0.2,
            "top_p": 0.95,
            "repetitions": 2,
            "notes": "示例测试",
        },
    )
    assert create_resp.status_code == 201
    test_prompt = create_resp.json()
    assert test_prompt["status"] == "completed"
    assert test_prompt["prompt_version_id"] == prompt_version_id
    assert test_prompt["prompt_version"]["version"] == "v1"
    assert test_prompt["prompt"]["name"] == prompt_payload["name"]

    list_resp = client.get("/api/v1/test_prompt/")
    assert list_resp.status_code == 200
    results = list_resp.json()
    assert len(results) == 1
    assert results[0]["id"] == test_prompt["id"]

    detail_resp = client.get(f"/api/v1/test_prompt/{test_prompt['id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["prompt_version"]["id"] == prompt_version_id
    assert detail["prompt"]["id"] == prompt_payload["id"]
    assert len(detail["results"]) == 2
    assert all(result["run_index"] in (1, 2) for result in detail["results"])
    assert detail["results"][0]["tokens_used"] is not None

    list_results_resp = client.get(f"/api/v1/test_prompt/{test_prompt['id']}/results")
    assert list_results_resp.status_code == 200
    results_payload = list_results_resp.json()
    assert len(results_payload) == 2
    assert {item["run_index"] for item in results_payload} == {1, 2}
