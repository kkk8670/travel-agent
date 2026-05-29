# app/models/openai_llm.py

"""
OpenAI 兼容格式的 provider

兼容主流 LLM 服务：
- OpenAI 官方（云）
- Ollama（本地）
- vLLM（本地/自建）
- groq / together.ai / fireworks / LM Studio ...（第三方托管）

它们差异在三个连接参数：base_url、api_key、model

例外厂商是 Anthropic，单独放 anthropic_provider.py。
"""

import json
from openai import OpenAI
from .base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """
    此类涵盖所有 OpenAI 兼容服务。

    参数:
        model: 模型名（如 'gpt-4o' / 'qwen2.5:7b' / 'Qwen/Qwen2.5-7B-Instruct'）
        base_url: 服务地址。None=OpenAI 官方；本地服务传 localhost 地址
        api_key: 云服务传真 key；本地服务传占位符即可


    这里【_内部函数】是将本系统的参数格式转化成openAI 硬性要求的JSON Schema 

	    OpenAI 要求请求参数包含：（调用 self.client.chat.completions.create(...) 时）
	    - 必须包含：model（指定模型）和 messages（对话历史数组）
	    - 可选但用工具必传：tools（工具列表）
	    - 其他常用参数：temperature（随机度）、max_tokens（最大生成长度）


    【_response】是 将返回的openAI的Schema转化成内部需要的格式 


    本地发出chat，大模型返回response，这中间LLM model做了：
    1. 语法检查与上下文组装：格式校验 + 拼接 Prompt
    2. 计算attention：把用户的 query 和 每个工具的描述（description）放在一起进行语义关联度计算。
    3. 内部决策：下一步做什么。belike 聊天还是调用工具。
    4. 实体识别与参数提取
    5. 组装成 json schema
    6. 返回response
    """

    def __init__(self, model: str, base_url: str | None = None, api_key: str = ""):
        self.model = model
        self.base_url = base_url
        self.client = OpenAI(base_url=base_url, api_key=api_key or "placeholder")


    def chat(self, messages, tools, system=""):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._to_openai_messages(messages, system),
            tools=self._to_openai_tools(tools) if tools else None,
            max_tokens=2048,
        )
        return self._parse_response(response)


    def _to_openai_tools(self, tools):
    	"""
    	把内部 tool 定义转成 OpenAI 要求的 function schema

		Tool（工具）：写好并暴露给 AI 的 Python 函数

    	OpenAI 硬性要求的 Tools 的 Schema：
	    [
	        {
	            "type": "function",
	            "function": {
	                "name": "工具名字",
	                "description": "工具的详细描述",        # <- AI靠这个识别
	                "parameters": { ... } # 严格的 JSON Schema 参数定义
	            }
	        }
	    ]
    	"""

        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in tools
        ]


    def _to_openai_messages(self, messages, system):
    	"""
    	把内部消息格式/其他provider格式转成 OpenAI message schema

		OpenAI 的 messages 硬性标准格式：
		messages 必须是一个数组/列表，里面的每一个元素都是一个字典，且必须包含 role 和 content
		[
		  {
		    "role": "system",
		    "content": "你是一个天气助手。"
		  },
		  {
		    "role": "user",
		    "content": "北京今天天气怎么样？"
		  }
		]

		其中，role 只有四个选项
		- system：系统全局设定。定义 AI 的人设、规矩。通常放在 messages 的第一条。
		- user：真实用户（问的问题）
		- assistant：AI 助手本身。ai如果想说话/调用工具，则用这个
		- tool：外部工具。即工具执行结果的角色
    	"""

        result = []
        if system:
            result.append({"role": "system", "content": system})
        for msg in messages:
            if isinstance(msg["content"], list):
                for block in msg["content"]:
                    if hasattr(block, "type"):  # Anthropic raw_content 对象
                        if block.type == "text":
                            result.append({"role": "assistant", "content": block.text})
                        elif block.type == "tool_use":
                            result.append({
                                "role": "assistant",
                                "tool_calls": [{
                                    "id": block.id,
                                    "type": "function",
                                    "function": {"name": block.name, "arguments": json.dumps(block.input)},
                                }],
                            })
                    elif isinstance(block, dict) and block.get("type") == "tool_result":
                        result.append({
                            "role": "tool",
                            "tool_call_id": block["tool_use_id"],
                            "content": block["content"],
                        })
            else:
                result.append(msg)
        return result


    def _parse_response(self, response):
    	"""
    	把 OpenAI 返回结果转回此系统内部统一格式

		原始的openAI 返回的消息格式：
		{
		  "id": "chatcmpl-123",
		  "object": "chat.completion",
		  "choices": [
		    {
		      "index": 0,
		      "message": {
		        "role": "assistant",
		        "content": null,
		        "tool_calls": [
		          {
		            "id": "call_abc123",
		            "type": "function",
		            "function": {
		              "name": "get_weather",
		              "arguments": "{\"location\": \"北京\"}"
		            }
		          }
		        ]
		      },
		      "finish_reason": "tool_calls"
		    }
		  ]
		}
    	"""

        message = response.choices[0].message
        result = {
            "content": message.content or "",
            "tool_calls": [],
            "stop_reason": "tool_use" if message.tool_calls else "end_turn",
            "raw_content": message,
        }
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {}  # 本地小模型偶尔输出不规范 JSON，兜底
                result["tool_calls"].append({
                    "id": tc.id or "call_0",
                    "name": tc.function.name,
                    "arguments": args,
                })
        return result