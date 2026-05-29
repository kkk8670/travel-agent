# app/models/__init__.py

"""
模型/Provider 层 (Model Layer)

对不同 LLM provider 的统一抽象，方便切换模型。

四个概念:
  - Inference Server 推理服务器，加载模型并提供 API（Ollama / vLLM 等）
  - Framework        编排 agent（本项目自研的 app/agents）
  - Provider         API 接入点/格式（本文件的两个 provider 类）
  - Model            真正的神经网络权重（Qwen2.5-7B 等）
"""

from .base import LLMProvider
from .anthropic_provider import AnthropicProvider
from .openai_compatible_provider import OpenAICompatibleProvider
from .fallback import FallbackProvider
from .factory import create_llm, create_router, create_provider, available_backends

# _openai_compatible 的 OpenAICompatibleProvider 是内部基类，不导出。
# 用户用具体子类（OpenAIProvider / OllamaProvider / VLLMProvider）。

__all__ = [
    "LLMProvider",
    "AnthropicProvider",
    "OpenAICompatibleProvider",
    "FallbackProvider",
    # 工厂（推荐用这两个）
    "create_llm",
    "create_router",
    # 偶尔需要直接造时用
    "create_provider",
    "available_backends",
]