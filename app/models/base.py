# app/models/base.py

"""
LLM provider 抽象

这里应该明确，自己系统的参数的schema：

1. 消息历史（Messages）的系统内部格式
    - 一条普通的用户文本消息：
        msg_text = {
            "role": "user", 
            "content": "北京冷吗？"
        }

    - 一条包含工具调用（AI发出）的消息
    msg_tool_call = {
        "role": "assistant",
        "content": [
            # 注意！这里你用的是原生对象（有 .type 属性）或者特定字典
            # 例如具有 block.type == "tool_use" 的对象
        ]
    }

    - 一条包含工具执行结果（你还给AI）的消息
    msg_tool_result = {
        "role": "user", # 或者是系统特定的 role
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "call_xxx",
                "content": "北京今天25度"
            }
        ]
    }

2. 模型返回结果（Response）的系统内部统一格式（type：LLMResponse）
my_system_response = {
    "content": "AI说的话（如果没有则为空字符串）",
    "tool_calls": [
        {
            "id": "工具调用的唯一ID",
            "name": "工具的名字（如 get_weather）",
            "arguments": {} # 强制要求：必须是一个已经解析好的 Python 字典！
        }
    ],
    "stop_reason": "结束原因（'tool_use' 或 'end_turn'）",
    "raw_content": "大模型厂商原始的、没动过的响应对象（留作备用）"
}

3. Tools 定义
t = {
    "name": "get_weather",
    "description": "查天气",
    "parameters": {             # 你的系统硬性规定叫 parameters
        "type": "object",       # 世界二的类型：代表参数是一个字典
        "properties": {
            "location": {"type": "string"} # 世界二的类型：代表位置是字符串
        }
    }
}
"""

from abc import ABC, abstractmethod
from app.common import ToolSchema, LLMResponse


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
