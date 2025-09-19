from datetime import timedelta
from typing import Any

import httpx

from app.models.llm_provider import LLMProvider


def create_provider(client, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post("/api/v1/llms/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_openai_provider_without_url(client):
    payload = {
        "provider_name": "OpenAI",
        "model_name": "gpt-4o",
        "api_key": "test-key",
        "parameters": {"temperature": 0.3, "max_tokens": 128},
    }
    provider = create_provider(client, payload)

    assert provider["base_url"] == "https://api.openai.com/v1"
    assert provider["is_custom"] is False
    assert provider["parameters"]["temperature"] == 0.3


def test_create_custom_provider_requires_url(client):
    payload = {
        "provider_name": "MyCustom",
        "model_name": "mistral",
        "api_key": "secret",
    }
    response = client.post("/api/v1/llms/", json=payload)
    assert response.status_code == 400
    assert "自定义提供者必须提供基础 URL" in response.text


def test_create_custom_with_emoji_logo(client):
    payload = {
        "provider_name": "CustomVendor",
        "model_name": "local-model",
        "api_key": "secret",
        "base_url": "https://llm.internal/api/",
        "logo_emoji": "🧠",
        "parameters": {"temperature": 0.7},
    }
    provider = create_provider(client, payload)

    assert provider["base_url"] == "https://llm.internal/api"
    assert provider["logo_emoji"] == "🧠"
    assert provider["is_custom"] is True


# 场景：非自定义且未知厂商缺少 base_url 时应返回 400
def test_create_non_custom_unknown_provider_requires_base_url(client):
    payload = {
        "provider_name": "LegacyVendor",
        "model_name": "legacy-model",
        "api_key": "secret",
        "is_custom": False,
    }
    response = client.post("/api/v1/llms/", json=payload)
    assert response.status_code == 400
    assert "该提供者需要配置基础 URL" in response.text


# 场景：验证列表接口的分页参数与模糊过滤
def test_list_llms_supports_pagination_and_filter(client):
    openai = create_provider(
        client,
        {
            "provider_name": "OpenAI",
            "model_name": "gpt-4o-mini",
            "api_key": "key",
        },
    )
    create_provider(
        client,
        {
            "provider_name": "CustomVendor",
            "model_name": "local-model",
            "api_key": "secret",
            "base_url": "https://llm.internal/api",
            "is_custom": True,
        },
    )

    response_all = client.get("/api/v1/llms/?limit=10&offset=0")
    assert response_all.status_code == 200
    assert any(item["id"] == openai["id"] for item in response_all.json())

    response_filtered = client.get("/api/v1/llms/?provider=Custom")
    assert response_filtered.status_code == 200
    filtered = response_filtered.json()
    assert len(filtered) == 1
    assert filtered[0]["provider_name"] == "CustomVendor"


# 场景：通过 ID 获取单个 LLM 提供者信息
def test_get_llm_returns_single_provider(client):
    provider = create_provider(
        client,
        {
            "provider_name": "Anthropic",
            "model_name": "claude-3",
            "api_key": "anthropic-key",
        },
    )

    response = client.get(f"/api/v1/llms/{provider['id']}")
    assert response.status_code == 200
    assert response.json()["provider_name"] == "Anthropic"


# 场景：查询不存在的提供者应返回 404
def test_get_llm_not_found(client):
    response = client.get("/api/v1/llms/9999")
    assert response.status_code == 404
    assert "未找到指定的提供者" in response.text


def test_update_disallows_logo_emoji_for_known_provider(client):
    provider = create_provider(
        client,
        {
            "provider_name": "OpenAI",
            "model_name": "gpt-4",
            "api_key": "key",
        },
    )

    response = client.put(f"/api/v1/llms/{provider['id']}", json={"logo_emoji": "🤖"})
    assert response.status_code == 400
    assert "仅允许自定义提供者设置 logo 表情符号" in response.text


# 场景：重复创建相同配置的提供者时触发唯一性校验
def test_create_duplicate_provider_conflict(client):
    payload = {
        "provider_name": "OpenAI",
        "model_name": "gpt-4",
        "api_key": "dup-key",
    }
    create_provider(client, payload)

    response = client.post("/api/v1/llms/", json=payload)
    assert response.status_code == 400
    assert "已存在具有相同名称、模型和基础 URL 的提供者" in response.text


# 场景：更新时允许清空参数并规范化 base_url
def test_update_llm_clears_parameters_and_normalizes_base_url(client):
    provider = create_provider(
        client,
        {
            "provider_name": "CustomVendor",
            "model_name": "model-a",
            "api_key": "secret",
            "base_url": "https://custom.llm/api",
            "is_custom": True,
            "parameters": {"temperature": 0.5},
        },
    )

    response = client.put(
        f"/api/v1/llms/{provider['id']}",
        json={
            "base_url": "https://custom.llm/api/",  # ensure normalization occurs
            "model_name": "model-b",
            "parameters": None,
        },
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["model_name"] == "model-b"
    assert updated["base_url"] == "https://custom.llm/api"
    assert updated["parameters"] == {}


# 场景：更新为与其他记录相同的组合应报重复错误
def test_update_llm_detects_duplicate_combination(client):
    primary = create_provider(
        client,
        {
            "provider_name": "OpenAI",
            "model_name": "gpt-4",
            "api_key": "primary",
        },
    )
    secondary = create_provider(
        client,
        {
            "provider_name": "CustomVendor",
            "model_name": "model-a",
            "api_key": "secondary",
            "base_url": "https://custom.llm/api",
            "is_custom": True,
        },
    )

    response = client.put(
        f"/api/v1/llms/{secondary['id']}",
        json={
            "provider_name": primary["provider_name"],
            "model_name": primary["model_name"],
            "base_url": primary["base_url"],
            "is_custom": False,
        },
    )
    assert response.status_code == 400
    assert "已存在具有相同名称、模型和基础 URL 的提供者" in response.text


# 场景：删除后再次查询应返回 404
def test_delete_llm_removes_provider(client):
    provider = create_provider(
        client,
        {
            "provider_name": "Anthropic",
            "model_name": "claude-3-opus",
            "api_key": "del-key",
        },
    )

    response = client.delete(f"/api/v1/llms/{provider['id']}")
    assert response.status_code == 204

    follow_up = client.get(f"/api/v1/llms/{provider['id']}")
    assert follow_up.status_code == 404


def test_invoke_llm_uses_openai_schema(client, monkeypatch):
    provider = create_provider(
        client,
        {
            "provider_name": "OpenAI",
            "model_name": "gpt-4",
            "api_key": "invoke-key",
            "parameters": {"temperature": 0.1},
        },
    )

    captured: dict[str, Any] = {}

    class DummyResponse:
        status_code = 200

        def __init__(self) -> None:
            self.elapsed = timedelta(milliseconds=12)

        def json(self) -> dict[str, Any]:
            return {
                "id": "chatcmpl-123",
                "choices": [
                    {"message": {"content": "This is a sample completion"}},
                ],
            }

        @property
        def text(self) -> str:  # pragma: no cover - parity with httpx response
            return ""

    def fake_post(
        url: str, headers: dict[str, str], json: dict[str, Any], timeout: float
    ) -> DummyResponse:
        captured.update(
            {"url": url, "headers": headers, "json": json, "timeout": timeout}
        )
        return DummyResponse()

    monkeypatch.setattr("app.api.v1.endpoints.llms.httpx.post", fake_post)

    body = {
        "messages": [
            {"role": "system", "content": "You are a test"},
            {"role": "user", "content": "Hello"},
        ],
        "parameters": {"temperature": 0.2},
    }

    response = client.post(f"/api/v1/llms/{provider['id']}/invoke", json=body)
    assert response.status_code == 200
    assert response.json()["id"] == "chatcmpl-123"

    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer invoke-key"
    assert captured["json"]["model"] == "gpt-4"
    assert captured["json"]["messages"][0]["role"] == "system"
    assert captured["json"]["temperature"] == 0.2
    assert captured["timeout"] == 30.0


# 场景：没有可用 base_url 的供应商调用时返回 400
def test_invoke_llm_requires_configured_base_url(client, db_session):
    provider = LLMProvider(
        provider_name="LegacyVendor",
        model_name="legacy",
        api_key="legacy-key",
        is_custom=False,
        base_url=None,
        parameters={},
    )
    db_session.add(provider)
    db_session.commit()

    body = {
        "messages": [{"role": "user", "content": "Ping"}],
        "parameters": {},
    }
    response = client.post(f"/api/v1/llms/{provider.id}/invoke", json=body)
    assert response.status_code == 400
    assert "该提供者未配置基础 URL" in response.text


# 场景：HTTPX 抛出超时异常时返回 502
def test_invoke_llm_handles_httpx_error(client, monkeypatch):
    provider = create_provider(
        client,
        {
            "provider_name": "OpenAI",
            "model_name": "gpt-4",
            "api_key": "invoke-error",
        },
    )

    def fake_post(*_: Any, **__: Any) -> None:
        raise httpx.TimeoutException("request timed out")

    monkeypatch.setattr("app.api.v1.endpoints.llms.httpx.post", fake_post)

    body = {
        "messages": [{"role": "user", "content": "Hello"}],
        "parameters": {},
    }
    response = client.post(f"/api/v1/llms/{provider['id']}/invoke", json=body)
    assert response.status_code == 502
    assert "request timed out" in response.text


# 场景：上游返回 JSON 错误体时需透传详情
def test_invoke_llm_propagates_error_payload(client, monkeypatch):
    provider = create_provider(
        client,
        {
            "provider_name": "OpenAI",
            "model_name": "gpt-4",
            "api_key": "invoke-error",
        },
    )

    class DummyErrorResponse:
        status_code = 429

        def json(self) -> dict[str, Any]:
            return {"error": {"message": "rate limited"}}

        @property
        def text(self) -> str:  # pragma: no cover - mirrors httpx
            return "rate limited"

    monkeypatch.setattr(
        "app.api.v1.endpoints.llms.httpx.post", lambda *_, **__: DummyErrorResponse()
    )

    body = {
        "messages": [{"role": "user", "content": "Hello"}],
        "parameters": {},
    }
    response = client.post(f"/api/v1/llms/{provider['id']}/invoke", json=body)
    assert response.status_code == 429
    assert response.json()["detail"]["error"]["message"] == "rate limited"


# 场景：已知厂商缺失 base_url 时应回落到内置默认值
def test_invoke_llm_uses_fallback_base_url_for_known_provider(
    client, db_session, monkeypatch
):
    provider = LLMProvider(
        provider_name="OpenAI",
        model_name="gpt-4",
        api_key="fallback",
        is_custom=False,
        base_url=None,
        parameters={},
    )
    db_session.add(provider)
    db_session.commit()

    captured: dict[str, Any] = {}

    class DummyResponse:
        status_code = 200

        def __init__(self) -> None:
            self.elapsed = timedelta(milliseconds=8)

        def json(self) -> dict[str, Any]:
            return {"choices": []}

        @property
        def text(self) -> str:  # pragma: no cover - mirrors httpx
            return ""

    def fake_post(
        url: str, headers: dict[str, str], json: dict[str, Any], timeout: float
    ) -> DummyResponse:
        captured.update(
            {"url": url, "headers": headers, "json": json, "timeout": timeout}
        )
        return DummyResponse()

    monkeypatch.setattr("app.api.v1.endpoints.llms.httpx.post", fake_post)

    body = {
        "messages": [{"role": "user", "content": "Hello"}],
        "parameters": {},
    }
    response = client.post(f"/api/v1/llms/{provider.id}/invoke", json=body)
    assert response.status_code == 200
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer fallback"


# 场景：上游返回非 JSON 错误内容时生成文本详情
def test_invoke_llm_handles_non_json_error_body(client, monkeypatch):
    provider = create_provider(
        client,
        {
            "provider_name": "OpenAI",
            "model_name": "gpt-4",
            "api_key": "invoke-error",
        },
    )

    class DummyTextResponse:
        status_code = 500

        def json(self) -> dict[str, Any]:  # pragma: no cover - intentional failure path
            raise ValueError("invalid json")

        @property
        def text(self) -> str:  # pragma: no cover - mirrors httpx
            return "Service unavailable"

    monkeypatch.setattr(
        "app.api.v1.endpoints.llms.httpx.post", lambda *_, **__: DummyTextResponse()
    )

    body = {
        "messages": [{"role": "user", "content": "Hello"}],
        "parameters": {},
    }
    response = client.post(f"/api/v1/llms/{provider['id']}/invoke", json=body)
    assert response.status_code == 500
    assert response.json()["detail"]["message"] == "Service unavailable"


# 场景：上游响应结构异常时仍返回原始 JSON
def test_invoke_llm_handles_unexpected_payload_structure(client, monkeypatch):
    provider = create_provider(
        client,
        {
            "provider_name": "OpenAI",
            "model_name": "gpt-4",
            "api_key": "invoke-weird",
        },
    )

    class BrokenDict(dict):
        def get(self, key, default=None):  # type: ignore[override]
            raise AttributeError("broken mapping")

    class DummyWeirdResponse:
        status_code = 200

        def json(self) -> BrokenDict:
            return BrokenDict({"unexpected": "format"})

        @property
        def text(self) -> str:  # pragma: no cover - mirrors httpx
            return ""

    monkeypatch.setattr(
        "app.api.v1.endpoints.llms.httpx.post", lambda *_, **__: DummyWeirdResponse()
    )

    body = {
        "messages": [{"role": "user", "content": "Hello"}],
        "parameters": {},
    }
    response = client.post(f"/api/v1/llms/{provider['id']}/invoke", json=body)
    assert response.status_code == 200
    assert response.json() == {"unexpected": "format"}
