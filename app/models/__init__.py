# app/models/__init__.py

"""
模型/Provider 层 (Model Layer)

对不同 LLM provider 的统一抽象，方便切换模型。
"""

from .base import LLMProvider
from .anthropic import AnthropicProvider
# openAI

__all__ = ["LLMProvider", "AnthropicProvider"]