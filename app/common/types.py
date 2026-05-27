# app/common/types.py

"""
全局类型定义
"""
from typing import Any, Callable, TypedDict


class ToolSchema(TypedDict):
    """
    LLM 可见的工具声明：
    - 名称：工具唯一标识，供 LLM 选择/调用
    - 用途：给 LLM 的功能说明，用于决定是否使用工具
    - 参数定义：工具参数 schema，描述需要哪些输入

    是给模型看的Tool的“接口描述”，类型约束 
    """
    name: str
    description: str
    parameters: dict[str, Any]


class Tool(TypedDict):
    """
    完整工具对象：schema + 实际执行函数。

    execute：接收 LLM 给的参数（dict），返回字符串结果。
    是真正可执行的工具对象
    """

    name: str
    description: str
    parameters: dict[str, Any]
    execute: Callable[..., Any]
    # Callable 表示可执行函数：Callable[参数类型, 返回类型]
    # 这里是定义比较宽松，即[参数随便，返回类型随便]


class LLMResponse(TypedDict):
    """
    统一的 LLM 响应协议：
    - content: LLM 生成的文本内容
    - tool_calls: LLM 请求调用的工具及参数信息（可能一次调用多个）
    - stop_reason: 停止原因，决定agent下一步调用什么
    - raw_content: 保留 provider 原始协议，因为统一格式会丢原厂商信息。下轮对话时，必须把原始结构塞回去，否则破坏上下文。
    """

    content: str
    tool_calls: list[ToolCall]
    stop_reason: str  # "end_turn" | "tool_use" | "max_tokens" | ...
    raw_content: Any  # provider 原始内容，回填 messages 用