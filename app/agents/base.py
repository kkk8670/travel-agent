# app/agents/base.py

"""
Agent 抽象基类

只对外暴露这个接口
"""

"""
abc: python 的抽象基类, 
abstractmenthod 表示 这个方法必须被子类实现
"""
from abc import ABC, abstractmethod


class Agent(ABC):
    """
    Agent 抽象接口，从run接收用户提问的query

    name表示Agent 类应该有一个 name 属性，它是 str 类型， 但是不强制
    @abstractmethod 表示子类必须有run这个函数 
    """

    name: str 

    @abstractmethod
    def run(self, query: str) -> str:
        """
        执行任务，返回最终回复。

        这里必须为空，因为是抽象
        但是实际run里会跑：
        
        run(query):
            while 没结束:
                让 LLM 思考  ← 需要"LLM provider"这个零件
                如果 LLM 想调 tool → 执行  ← 需要"tool"这个零件
                如果 LLM 给出答案 → 返回
        """
        pass

    def describe(self) -> str:
        """简单描述，用于注册表展示等。子类可覆盖。"""
        return f"{self.name}"


# 这样使用：
if __name__ == "__main__":
    # 想象中的 main.py（不实际写）
    agent = some_factory()
    print(agent.run("帮我订机票"))
