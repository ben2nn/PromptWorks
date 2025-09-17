from typing import Any


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
    assert "Base URL is required" in response.text


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
    assert "Logo emoji" in response.text


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

        def json(self) -> dict[str, Any]:
            return {"id": "chatcmpl-123", "choices": []}

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
