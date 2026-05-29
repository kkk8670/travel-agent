# app/models/factory.py

"""
Provider 工厂：配置驱动地创建 provider。

解藕配置和切换provider

两层抽象
========
1. 上层（setting.py 的 LOCAL_PROFILES / CLOUD_PROFILES）：
   配置模型和推理服务器具体参数
   用户在 .env 里只选profiles类型。

2. 下层（本文件的 _BACKENDS）：
   每个 backend 对应一个具体的接入实现（class + base_url）。
   profile 选好后，setting 把 backend + model 喂给本文件。
"""


import os
from .base import LLMProvider
from .anthropic_provider import AnthropicProvider
from .openai_compatible_provider import OpenAICompatibleProvider
from app.config import setting
from .fallback import FallbackProvider


# 每个 backend :provider 类 + 默认连接参数。
# 可添加新provider配置
_BACKENDS = {
    # --- 云端 API ---
    "anthropic": dict(cls="anthropic",     base_url=None,                               needs_key="anthropic"),
    "openai":    dict(cls="openai_compat", base_url=None,                               needs_key="openai"),
    # --- 本地推理服务器（OpenAI 兼容）---
    "ollama":    dict(cls="openai_compat", base_url="http://localhost:11434/v1",        needs_key=None),
    "vllm":      dict(cls="openai_compat", base_url="http://localhost:8000/v1",         needs_key=None),
}


def create_provider(backend: str, model: str) -> LLMProvider:
    """根据 backend 名 + model 创建 provider。
    一般不直接用，调用方用 create_llm() / create_router() 更方便。"""
    if backend not in _BACKENDS:
        raise ValueError(
            f"未知 backend '{backend}'。可用: {list(_BACKENDS.keys())}"
        )

    config = _BACKENDS[backend]

    # base_url 允许被环境变量覆盖（连远程服务器、改端口等）
    base_url = os.getenv(f"{backend.upper()}_BASE_URL", config["base_url"])

    # 取 api key
    api_key = ""
    if config["needs_key"] == "anthropic":
        api_key = setting.anthropic_api_key
    elif config["needs_key"] == "openai":
        api_key = setting.openai_api_key

    # 造 provider
    if config["cls"] == "anthropic":
        return AnthropicProvider(model=model)
    else:  # openai_compat
        return OpenAICompatibleProvider(
            model=model,
            base_url=base_url,
            api_key=api_key,
        )


def create_llm() -> LLMProvider:
    """
    根据 setting 创建主 LLM provider。
    用户改 .env 的 LLM_TARGET / LOCAL_PROFILE / CLOUD_PROFILE 切换。
	若 enable_fallback=True，会包装成 FallbackProvider，主用挂了自动切本地 dev。
    """

    spec = setting.resolve_llm()
    primary = create_provider(spec["backend"], spec["model"])
    
    if not setting.enable_fallback:
        return primary
    
    # 备用永远是 local dev（本地兜底）
    backup_spec = setting.LOCAL_PROFILES["dev"]  # 从 setting import
    # 避免主备相同（用户主就是 local dev 时不用 fallback）
    if spec == backup_spec:
        return primary
    backup = create_provider(backup_spec["backend"], backup_spec["model"])
    return FallbackProvider([primary, backup])


def create_router() -> LLMProvider:
    """根据 setting 创建路由器 provider。"""
    spec = setting.resolve_router()
    return create_provider(spec["backend"], spec["model"])


def available_backends() -> list[str]:
    return list(_BACKENDS.keys())