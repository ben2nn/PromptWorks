from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class ProviderDefaults:
    key: str
    name: str
    base_url: str | None
    logo_emoji: str | None
    description: str | None = None
    logo_url: str | None = None


# 预置常用提供方信息，方便前端直接展示品牌内容
_COMMON_PROVIDERS: Dict[str, ProviderDefaults] = {
    "openai": ProviderDefaults(
        key="openai",
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        logo_emoji="🧠",
        description="通用对话与代码生成能力强，官方模型接入通道。",
    ),
    "anthropic": ProviderDefaults(
        key="anthropic",
        name="Anthropic",
        base_url="https://api.anthropic.com",
        logo_emoji="🤖",
        description="Claude 系列专注长文本与合规场景。",
    ),
    "azure-openai": ProviderDefaults(
        key="azure-openai",
        name="Azure OpenAI",
        base_url="https://{resource-name}.openai.azure.com",
        logo_emoji="☁️",
        description="基于 Azure 的企业级 OpenAI 服务，需自定义资源域名。",
    ),
    "google": ProviderDefaults(
        key="google",
        name="Google",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        logo_emoji="🔎",
        description="Gemini 系列涵盖多模态推理与搜索增强。",
    ),
}


def get_provider_defaults(provider_key: str | None) -> ProviderDefaults | None:
    if not provider_key:
        return None
    return _COMMON_PROVIDERS.get(provider_key.lower())


def iter_common_providers() -> Iterable[ProviderDefaults]:
    return _COMMON_PROVIDERS.values()
