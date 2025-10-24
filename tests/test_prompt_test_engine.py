from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from app.models.llm_provider import LLMModel, LLMProvider
from app.models.prompt import Prompt, PromptClass, PromptVersion
from app.models.prompt_test import (
    PromptTestExperiment,
    PromptTestExperimentStatus,
    PromptTestTask,
    PromptTestUnit,
)
from app.services import prompt_test_engine
from app.services.prompt_test_engine import execute_prompt_test_experiment


class DummyResponse:
    """用于伪造 httpx 返回值的简单封装。"""

    def __init__(self, payload: dict[str, Any], *, elapsed_ms: int | None) -> None:
        self._payload = payload
        self.status_code = 200
        self.elapsed = (
            timedelta(milliseconds=elapsed_ms) if elapsed_ms is not None else None
        )

    def json(self) -> dict[str, Any]:
        return self._payload

    @property
    def text(self) -> str:
        return ""


def _create_prompt_version(db_session) -> PromptVersion:
    prompt_class = PromptClass(name="测试类")
    prompt = Prompt(name="翻译测试", prompt_class=prompt_class)
    version = PromptVersion(
        prompt=prompt, version="v1", content="你是一位严谨的翻译助手。"
    )
    prompt.current_version = version
    db_session.add_all([prompt_class, prompt, version])
    db_session.commit()
    return version


def _create_provider_and_model(
    db_session, *, base_url: str | None = "https://llm.fake/api"
) -> LLMModel:
    provider = LLMProvider(
        provider_name="Internal",
        provider_key=None,
        api_key="fake-key",
        is_custom=True,
        base_url=base_url,
    )
    model = LLMModel(provider=provider, name="chat-mini")
    db_session.add_all([provider, model])
    db_session.commit()
    return model


def test_execute_prompt_test_experiment_generates_metrics(db_session, monkeypatch):
    prompt_version = _create_prompt_version(db_session)
    model = _create_provider_and_model(db_session)
    provider = model.provider

    task = PromptTestTask(name="翻译基准测试", prompt_version_id=prompt_version.id)
    unit = PromptTestUnit(
        task=task,
        prompt_version_id=prompt_version.id,
        name="中文翻译英文",
        model_name=model.name,
        llm_provider_id=provider.id,
        rounds=2,
        prompt_template="请翻译：{text}",
        variables={"cases": [{"text": "你好"}, {"text": "谢谢"}]},
        parameters={"max_tokens": 32},
    )
    experiment = PromptTestExperiment(unit=unit, sequence=1)

    db_session.add_all([task, unit, experiment])
    db_session.commit()

    def fake_post(*_, **kwargs):
        payload = kwargs.get("json") or {}
        messages = payload.get("messages") or []
        user_text = messages[-1]["content"] if messages else ""
        if "你好" in user_text:
            response = {
                "choices": [{"message": {"content": "Hello"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 4},
            }
            return DummyResponse(response, elapsed_ms=18)
        response = {
            "choices": [{"message": {"content": '{"value":"Thanks"}'}}],
            "usage": {"total_tokens": 16},
        }
        return DummyResponse(response, elapsed_ms=24)

    monkeypatch.setattr("app.services.prompt_test_engine.httpx.post", fake_post)

    execute_prompt_test_experiment(db_session, experiment)
    db_session.commit()

    refreshed = db_session.get(PromptTestExperiment, experiment.id)
    assert refreshed.status == PromptTestExperimentStatus.COMPLETED
    assert refreshed.outputs is not None and len(refreshed.outputs) == 4
    assert refreshed.outputs[0]["output_text"] == "Hello"
    assert refreshed.outputs[1]["parsed_output"] == {"value": "Thanks"}
    assert refreshed.outputs[2]["output_text"] == "Hello"
    assert refreshed.outputs[3]["parsed_output"] == {"value": "Thanks"}
    assert [item["variables"] for item in refreshed.outputs] == [
        {"text": "你好"},
        {"text": "谢谢"},
        {"text": "你好"},
        {"text": "谢谢"},
    ]

    metrics = refreshed.metrics
    assert metrics and metrics["rounds"] == 4
    assert metrics["json_success_rate"] == pytest.approx(0.5, rel=1e-3)
    assert metrics["avg_latency_ms"] > 0


def test_prompt_test_api_creates_and_executes_experiment(
    client, db_session, monkeypatch
):
    prompt_version = _create_prompt_version(db_session)
    model = _create_provider_and_model(db_session)
    provider = model.provider

    def fake_post(*_, **kwargs):
        response = {
            "choices": [{"message": {"content": "Hello World"}}],
            "usage": {"prompt_tokens": 4, "completion_tokens": 5},
        }
        return DummyResponse(response, elapsed_ms=10)

    monkeypatch.setattr("app.services.prompt_test_engine.httpx.post", fake_post)

    response = client.post(
        "/api/v1/prompt-test/tasks",
        json={
            "name": "集成实验",
            "prompt_version_id": prompt_version.id,
            "units": [
                {
                    "name": "翻译单元",
                    "model_name": model.name,
                    "llm_provider_id": provider.id,
                    "rounds": 1,
                    "prompt_template": "翻译：{text}",
                    "variables": {"text": "你好"},
                    "parameters": {"max_tokens": 16},
                }
            ],
        },
    )
    assert response.status_code == 201
    task_id = response.json()["id"]

    unit_resp = client.get(f"/api/v1/prompt-test/tasks/{task_id}/units")
    assert unit_resp.status_code == 200
    unit_list = unit_resp.json()
    assert len(unit_list) == 1
    unit_id = unit_list[0]["id"]

    experiment_resp = client.post(
        f"/api/v1/prompt-test/units/{unit_id}/experiments",
        json={"auto_execute": True, "batch_id": "batch-1"},
    )
    assert experiment_resp.status_code == 201
    body = experiment_resp.json()
    assert body["status"] == PromptTestExperimentStatus.COMPLETED.value
    assert body["metrics"]["rounds"] == 1
    assert body["outputs"][0]["output_text"] == "Hello World"
    assert body["outputs"][0]["variables"] == {"text": "你好"}

    detail_resp = client.get(f"/api/v1/prompt-test/experiments/{body['id']}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["status"] == PromptTestExperimentStatus.COMPLETED.value
