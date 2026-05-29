# app/config/settings.py

"""
配置集中管理。
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 在读任何环境变量之前先加载 .env，保证 app.config 一被 import，.env 就就绪
load_dotenv()

# 本地推理服务器的 profile
# key 在 .env 选择 
LOCAL_PROFILES = {
    "dev":  {"backend": "ollama", "model": "qwen2.5:7b"},
    "prod": {"backend": "vllm",   "model": "Qwen/Qwen2.5-7B-Instruct"},
}

# 云端 API 的 profile
CLOUD_PROFILES = {
    "anthropic": {"backend": "anthropic", "model": "claude-sonnet-4-5"},
    "openai":    {"backend": "openai",    "model": "gpt-4o"},
}

# 路由器单独配置（路由任务简单，用便宜的小模型）
ROUTER_PROFILES = {
    "cloud": {"backend": "anthropic", "model": "claude-haiku-4-5-20251001"},
    "local": {"backend": "ollama",    "model": "qwen2.5:7b"},
}


@dataclass
class Settings:
    # === 主 LLM ===
    # local 或 cloud：选要不要走本地
    llm_target: str = "local"
    # 选完上面，下面这个决定具体走哪个 profile
    local_profile: str = "dev"        # dev 或 prod
    cloud_profile: str = "openai"  # anthropic 或 openai

    # === 路由 LLM ===
    router_target: str = "cloud"      # local 或 cloud

    # === API keys（只云端 profile 需要）===
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # === agent 行为 ===
    max_iterations: int = 12

    # === fallback 开关 ===
    # 当主 LLM 失败时是否自动切到备用。备用永远是 local + dev。
    # 用于断网/限流/付费方案省钱等场景。
    enable_fallback: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_target=os.getenv("LLM_TARGET", "cloud"),
            local_profile=os.getenv("LOCAL_PROFILE", "dev"),
            cloud_profile=os.getenv("CLOUD_PROFILE", "anthropic"),
            router_target=os.getenv("ROUTER_TARGET", "cloud"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            enable_fallback=os.getenv("ENABLE_FALLBACK", "false").lower() == "true",
        )

    def resolve_llm(self) -> dict:
        """根据 target + profile 解析出具体的 backend 和 model。"""
        if self.llm_target == "local":
            if self.local_profile not in LOCAL_PROFILES:
                raise ValueError(
                    f"未知 local_profile '{self.local_profile}'。"
                    f"可用: {list(LOCAL_PROFILES.keys())}"
                )
            return LOCAL_PROFILES[self.local_profile]
        elif self.llm_target == "cloud":
            if self.cloud_profile not in CLOUD_PROFILES:
                raise ValueError(
                    f"未知 cloud_profile '{self.cloud_profile}'。"
                    f"可用: {list(CLOUD_PROFILES.keys())}"
                )
            return CLOUD_PROFILES[self.cloud_profile]
        else:
            raise ValueError(
                f"LLM_TARGET 必须是 'local' 或 'cloud'，收到: '{self.llm_target}'"
            )

    def resolve_router(self) -> dict:
        """解析路由器用哪个 LLM。"""
        if self.router_target not in ROUTER_PROFILES:
            raise ValueError(
                f"未知 router_target '{self.router_target}'。"
                f"可用: {list(ROUTER_PROFILES.keys())}"
            )
        return ROUTER_PROFILES[self.router_target]


# 全局单例
setting = Settings.from_env()