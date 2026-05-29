# app/models/anthropic.py

"""
Anthropic provider 实现

本系统格式比较偏向anthropic的格式
"""

from anthropic import Anthropic
from app.config import setting
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    """
    Anthropic API 的硬性规定：（self.client.messages.create）
    - 必须包含：model（模型名）和 messages（对话历史）。
    - 必须包含：max_tokens（它不像 OpenAI 是可选的，Anthropic 强行要求必须传这个参数）。
    - 单独的参数：system（系统提示词）。OpenAI 是把 system 塞进 messages 列表里的，而 Anthropic 中，system 必须作为一个独立的顶级参数传入，绝对不能塞进 messages 里。


    Anthropic 对 messages 数组的规定:
    1. Role 限制:
        - 绝对不能有 system 角色
        - 绝对不能有 tool 角色
    2. 工具的返回结果（Tool Result）:
        Anthropic 规定：工具执行的结果，必须伪装成 user 说的话。
        这里引入了 Anthropic 的核心概念：Content Blocks（内容块）。它的 content 不仅可以是一段简单的字符串，还可以是一个列表（包含多个不同类型的 Block 字典）

    标准的输入硬性格式示例：
    [
      {
        "role": "user",
        "content": "北京天气怎么样？"
      },
      {
        "role": "assistant",
        "content": [
          {
            "type": "text",
            "text": "好的，我来帮你查一下。"
          },
          {
            "type": "tool_use",
            "id": "toolu_01AwwZDL2",
            "name": "get_weather",
            "input": {"location": "北京"}
          }
        ]
      },
      {
        "role": "user", 
        "content": [
          {
            "type": "tool_result",
            "tool_use_id": "toolu_01AwwZDL2",
            "content": "北京市今天晴，25度"
          }
        ]
      }
    ]
    其中消息内容类型的type只有这三种：
    - "text"：代表一段纯文本。
    - "tool_use"：代表大模型说“我要调用工具”。
    - "tool_result"：代表你本地执行完工具，把结果还给大模型。
    - (option) "type": "image"：如果你要发一张图片给 Claude 识别，图片块的类型就是这个。
    

    Tools 的硬性 JSON Schema:
    要求你传一个列表，每个工具都是一个字典，有三个硬性键（Key）：
    {
      "name": "工具名称",
      "description": "工具的详细功能描述，AI靠这个意图识别",
      "input_schema": {
        "type": "object",
        "properties": {
          "参数名": {"type": "类型", "description": "参数描述"}
        },
        "required": ["必填参数"]
      }
    }


    输出：response 的硬性标准：
    # response.content 的真实硬性结构（简化后的伪代码）
    [
        TextMessageBlock(type="text", text="正在为您查询..."),
        ToolUseBlock(type="tool_use", id="toolu_xxx", name="get_weather", input={"location": "北京"})
    ]


    """
    def __init__(self, model: str | None = None):
        self.client = Anthropic(api_key=setting.anthropic_api_key)
        self.model = model or setting.default_model

    def chat(self, messages, tools, system=""):
        anthropic_tools = [
            {
                "name": t["name"], 
                "description": t["description"], 
                "input_schema": t["parameters"]
            }
            for t in tools
        ]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=anthropic_tools if anthropic_tools else None,
        )

        result = {
            "content": "",
            "tool_calls": [],
            "stop_reason": response.stop_reason,
            "raw_content": response.content,
        }
        for block in response.content:
            if block.type == "text":
                result["content"] += block.text
            elif block.type == "tool_use":
                result["tool_calls"].append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input,
                })
        return result