# app/models/base.py

"""
LLM provider 抽象
"""

from abc import ABC, abstractmethod
from ..common import ToolSchema, LLMResponse


class LLMProvider(ABC):
    """所有 LLM 基层抽象类"""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: list[ToolSchema],
        system: str = "",
    ) -> LLMResponse:
        """
        发一次对话请求：
        - messages：对话历史上下文输入
        - tools：当前可供模型调用的工具列表（仅声明，不含执行逻辑）【不传 execute】
        - system：全局系统提示词，用于约束模型行为与输出规则
        """
        pass
