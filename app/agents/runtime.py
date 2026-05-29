# app/agents/runtime.py


"""
实现了 Agent 接口。标准的 ReAct (Reasoning and Acting) 架构

SingleAgent 内部是经典的 LLM tool-calling 循环:
把 LLM 当成大脑，把配置好的工具当成手脚，通过一个循环（Loop）让大脑和手脚不断协同，直到解决用户的问题。

SingleAgent可作为基本框架，如有不同agent需求，只用替换不同 system_prompt 和 tools 。

"""
from app.models import LLMProvider
from app.common import Tool
from .base import Agent


class SingleAgent(Agent):
    """
    SingleAgent: 通用的单 agent 实现
    一个 LLM + 一组 tool + 一个循环

    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: list[Tool],
        provider: LLMProvider,
        max_iterations: int = 10,
        indent_level: int = 0,
    ):
        """
        接收核心参数：
        - system_prompt:
        - tools:
        - provider:
        - max_iternations: 约束最多循环10次
        """

        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools
        self.provider = provider
        self.max_iterations = max_iterations
        self.indent = "  " * indent_level


    def _tool_schemas(self):
        """
        tool内容转化为本系统规定tool格式
        """

        return [
            {
                "name": t["name"], 
                "description": t["description"], 
                "parameters": t["parameters"]
            }
            for t in self.tools
        ]


    def _execute_tool(self, name: str, arguments: dict) -> str:
        """
        根据大模型发出的指令名字，去调用对应的 Python 函数。
        带 Self-correction 机制
        """

        for t in self.tools:
            if t["name"] == name:
                try:
                    return str(t["execute"](**arguments))
                except Exception as e:
                    # 不把原始 stack 喂给 LLM，包装成结构化错误
                    return f"Error: {type(e).__name__}: {e}"
        return f"Error: tool '{name}' not found"


    def run(self, query: str) -> str:
        """
        核心运行循环：
        1. 将用户提问放入message
        2. 调用大模型，通过self.provider.chat()，将历史记录、系统提示词和工具列表一起发给大模型。
        3. 终结条件判定，看stop_reason，决定是否退出循环给答案。
        4. 执行工具：
            如果模型需要工具（toll_calls有值），则返回所有工。
            -> 遍历这些tools，逐个执行，拿到结果
        5. 状态更新：把 tool_results 以 role: user 的身份追加到 messages 历史里，然后进入下一轮循环，让大模型基于新看到的结果继续思考。
             
        """

        messages: list[dict] = [{"role": "user", "content": query}]

        for i in range(self.max_iterations):
            print(f"{self.indent}[{self.name}] 第 {i+1} 轮 思考中...")

            response = self.provider.chat(
                messages=messages,
                tools=self._tool_schemas(),
                system=self.system_prompt,
            )

            stop = response["stop_reason"]

            # 把 assistant 回复加入历史（统一格式）
            if response["tool_calls"]:
                messages.append({
                    "role": "assistant",
                    "tool_calls": response["tool_calls"],
                })
            else:
                messages.append({
                    "role": "assistant",
                    "content": response["content"],
                })


            # 决定下一步
            if stop == "tool_use" and response["tool_calls"]:
                # 执行所有 tool，把结果加入历史
                for tc in response["tool_calls"]:
                    args_preview = str(tc["arguments"])[:120]
                    print(f"{self.indent}[{self.name}] → {tc['name']}({args_preview})")
                    result = self._execute_tool(tc["name"], tc["arguments"])
                    result_preview = result[:120].replace("\n", " ")
                    print(f"{self.indent}[{self.name}]   结果: {result_preview}...")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })
                continue
            elif stop == "max_tokens":
                print(f"{self.indent}[{self.name}] ⚠ 达到 token 上限")
                return response["content"]
            elif stop == "error":
                return f"[{self.name}] provider 报错，无法继续"
            else:
                preview = response["content"][:100].replace("\n", " ")
                print(f"{self.indent}[{self.name}] ✓ 完成: {preview}...")
                return response["content"]

        return f"[{self.name}] 达到最大轮数，未完成"


if __name__ == "__main__":
    # 跑法: uv run python -m app.agents.runtime
    from app.models import create_llm
    from app.tools import WEATHER_TOOLS

    agent = SingleAgent(
        name="WeatherBot",
        system_prompt="你是天气助手，回答简短",
        tools=WEATHER_TOOLS,
        provider=create_llm(),  # 用 settings 默认的 LLM
    )
    result = agent.run("东京 2026 年 6 月 1 日天气")
    print("\n最终结果:", result)
    assert result, "应该有结果"
    print("✓ SingleAgent 通过")