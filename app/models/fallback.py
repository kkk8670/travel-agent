# app/models/fallback.py


from .base import LLMProvider


class FallbackProvider(LLMProvider):
    def __init__(self, providers: list[LLMProvider]):
        if not providers:
            raise ValueError("至少需要一个 provider")
        self.providers = providers  # 按优先级排列，第一个是主用

    def chat(self, messages, tools, system=""):
        last_error = None
        for i, provider in enumerate(self.providers):
            try:
                return provider.chat(messages, tools, system)
            except Exception as e:
                last_error = e
                print(f"[Fallback] {type(provider).__name__} 失败: {e}，切换下一个")
                continue
        raise RuntimeError(f"所有 provider 都失败了，最后错误: {last_error}")