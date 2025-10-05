from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.task_queue import task_queue
from app.models.usage import LLMUsageLog
from app.services.test_run import TestRunExecutionError


def _create_prompt(client: TestClient) -> dict[str, Any]:
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


def _create_provider_with_model(
    client: TestClient,
) -> tuple[dict[str, Any], dict[str, Any]]:
    provider_resp = client.post(
        "/api/v1/llm-providers/",
        json={
            "provider_name": "Internal",
            "api_key": "test-secret",
            "is_custom": True,
            "base_url": "https://llm.internal/api",
            "logo_emoji": "🤖",
        },
    )
    assert provider_resp.status_code == 201
    provider = provider_resp.json()

    model_resp = client.post(
        f"/api/v1/llm-providers/{provider['id']}/models",
        json={"name": "chat-mini", "capability": "测试"},
    )
    assert model_resp.status_code == 201
    model = model_resp.json()
    assert model["name"] == "chat-mini"
    return provider, model


def test_create_test_prompt_requires_prompt_version(client: TestClient) -> None:
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


def test_create_and_retrieve_test_prompt(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    """验证测试任务创建后可通过列表和详情接口读取。"""

    provider, model = _create_provider_with_model(client)

    call_records: list[dict[str, Any]] = []

    class DummyResponse:
        status_code = 200

        def __init__(self, index: int) -> None:
            self._index = index
            self.elapsed = timedelta(milliseconds=150 + index)

        def json(self) -> dict[str, Any]:
            return {
                "choices": [
                    {"message": {"content": f"第 {self._index} 次响应内容"}},
                ],
                "usage": {
                    "prompt_tokens": 100 + self._index,
                    "completion_tokens": 20 + self._index,
                    "total_tokens": 120 + self._index,
                },
            }

        @property
        def text(self) -> str:
            return ""

    def fake_post(
        url: str, headers: dict[str, str], json: dict[str, Any], timeout: float
    ):
        call_index = len(call_records) + 1
        call_records.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )
        return DummyResponse(call_index)

    monkeypatch.setattr("app.services.test_run.httpx.post", fake_post)

    prompt_payload = _create_prompt(client)
    prompt_version_id = prompt_payload["current_version"]["id"]

    create_resp = client.post(
        "/api/v1/test_prompt/",
        json={
            "prompt_version_id": prompt_version_id,
            "model_name": model["name"],
            "model_version": provider["provider_name"],
            "temperature": 0.2,
            "top_p": 0.95,
            "repetitions": 2,
            "notes": "示例测试",
            "schema": {
                "inputs": ["第一轮提问", "第二轮提问"],
                "llm_parameters": {"max_tokens": 64},
                "job_name": "示例 A/B 测试",
            },
        },
    )
    assert create_resp.status_code == 201
    test_prompt = create_resp.json()
    initial_status = test_prompt["status"]
    assert initial_status in {"pending", "running", "completed"}
    if initial_status != "completed":
        assert test_prompt["results"] == []
    assert test_prompt["prompt_version_id"] == prompt_version_id
    assert test_prompt["prompt_version"]["version"] == "v1"
    assert test_prompt["prompt"]["name"] == prompt_payload["name"]

    assert len(call_records) == 2
    for index, record in enumerate(call_records, start=1):
        assert record["url"].endswith("/chat/completions")
        assert record["headers"]["Authorization"].startswith("Bearer test-secret")
        assert record["json"]["model"] == model["name"]
        assert record["json"]["max_tokens"] == 64
        assert record["json"]["temperature"] == 0.2
        assert record["json"]["messages"][0]["role"] == "system"
        assert (
            record["json"]["messages"][0]["content"]
            == prompt_payload["current_version"]["content"]
        )
        assert (
            record["json"]["messages"][1]["content"]
            == ["第一轮提问", "第二轮提问"][index - 1]
        )

    assert task_queue.wait_for_idle(timeout=2.0)

    list_resp = client.get("/api/v1/test_prompt/")
    assert list_resp.status_code == 200
    results = list_resp.json()
    assert len(results) == 1
    assert results[0]["id"] == test_prompt["id"]
    assert results[0]["status"] == "completed"

    detail_resp = client.get(f"/api/v1/test_prompt/{test_prompt['id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["status"] == "completed"
    assert detail["prompt_version"]["id"] == prompt_version_id
    assert detail["prompt"]["id"] == prompt_payload["id"]
    assert len(detail["results"]) == 2
    assert (
        detail["schema"]["prompt_snapshot"]
        == prompt_payload["current_version"]["content"]
    )

    sorted_results = sorted(detail["results"], key=lambda item: item["run_index"])
    assert sorted_results[0]["run_index"] == 1
    assert sorted_results[0]["tokens_used"] == 121
    assert sorted_results[0]["latency_ms"] == 151
    assert sorted_results[1]["run_index"] == 2
    assert sorted_results[1]["tokens_used"] == 122
    assert sorted_results[1]["latency_ms"] == 152

    list_results_resp = client.get(f"/api/v1/test_prompt/{test_prompt['id']}/results")
    assert list_results_resp.status_code == 200
    results_payload = list_results_resp.json()
    assert len(results_payload) == 2
    assert {item["run_index"] for item in results_payload} == {1, 2}

    usage_logs = list(
        db_session.scalars(
            select(LLMUsageLog).where(
                LLMUsageLog.prompt_version_id == prompt_version_id,
                LLMUsageLog.source == "test_run",
            )
        )
    )
    assert len(usage_logs) == 2
    assert all(log.source == "test_run" for log in usage_logs)
    assert all(log.model_name == model["name"] for log in usage_logs)


def test_create_test_prompt_handles_service_error(client: TestClient, monkeypatch):
    prompt_payload = _create_prompt(client)
    prompt_version_id = prompt_payload["current_version"]["id"]

    def raise_error(*_, **__):
        raise TestRunExecutionError("执行失败", status_code=422)

    monkeypatch.setattr("app.core.task_queue.execute_test_run", raise_error)

    response = client.post(
        "/api/v1/test_prompt/",
        json={
            "prompt_version_id": prompt_version_id,
            "model_name": "gpt-error",
            "temperature": 0.1,
            "top_p": 0.9,
            "repetitions": 1,
        },
    )
    assert response.status_code == 201

    assert task_queue.wait_for_idle(timeout=2.0)

    detail_resp = client.get(f"/api/v1/test_prompt/{response.json()['id']}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["status"] == "failed"
    assert detail["schema"].get("last_error") == "执行失败"


def test_update_test_prompt_allows_partial_fields(client: TestClient, monkeypatch):
    prompt_payload = _create_prompt(client)
    prompt_version_id = prompt_payload["current_version"]["id"]

    def fake_execute(db, test_run):
        test_run.status = "completed"
        return test_run

    monkeypatch.setattr("app.core.task_queue.execute_test_run", fake_execute)

    create_resp = client.post(
        "/api/v1/test_prompt/",
        json={
            "prompt_version_id": prompt_version_id,
            "model_name": "gpt-4o",
            "temperature": 0.2,
            "top_p": 0.9,
            "repetitions": 1,
        },
    )
    test_run = create_resp.json()

    assert task_queue.wait_for_idle(timeout=2.0)

    patch_resp = client.patch(
        f"/api/v1/test_prompt/{test_run['id']}",
        json={"notes": "更新说明", "status": "failed"},
    )
    assert patch_resp.status_code == 200
    payload = patch_resp.json()
    assert payload["notes"] == "更新说明"
    assert payload["status"] == "failed"


def test_get_test_prompt_not_found(client: TestClient):
    resp = client.get("/api/v1/test_prompt/9999")
    assert resp.status_code == 404
