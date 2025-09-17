from fastapi.testclient import TestClient


def _create_prompt(client: TestClient) -> int:
    response = client.post(
        "/api/v1/prompts/",
        json={
            "name": "对话助手",
            "version": "v1",
            "content": "你是一位乐于助人的智能助手。",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_test_run_requires_prompt(client: TestClient):
    response = client.post(
        "/api/v1/test-runs/",
        json={
            "prompt_id": 999,
            "model_name": "gpt-4o",
            "temperature": 0.1,
            "top_p": 0.9,
            "repetitions": 1,
        },
    )
    assert response.status_code == 404


def test_create_and_retrieve_test_run(client: TestClient):
    prompt_id = _create_prompt(client)

    create_resp = client.post(
        "/api/v1/test-runs/",
        json={
            "prompt_id": prompt_id,
            "model_name": "gpt-4o",
            "model_version": "2024-05-01",
            "temperature": 0.2,
            "top_p": 0.95,
            "repetitions": 2,
            "notes": "示例测试",
        },
    )
    assert create_resp.status_code == 201
    test_run = create_resp.json()
    assert test_run["status"] == "pending"
    assert test_run["prompt_id"] == prompt_id

    list_resp = client.get("/api/v1/test-runs/")
    assert list_resp.status_code == 200
    results = list_resp.json()
    assert len(results) == 1
    assert results[0]["id"] == test_run["id"]

    detail_resp = client.get(f"/api/v1/test-runs/{test_run['id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["prompt"]["id"] == prompt_id
    assert detail["results"] == []

    list_results_resp = client.get(f"/api/v1/test-runs/{test_run['id']}/results")
    assert list_results_resp.status_code == 200
    assert list_results_resp.json() == []
