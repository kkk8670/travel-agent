# Travel Agent

一个旅行助手 demo。架构按生产级 agent 项目的常见规范组织：
- 按业务命名 agent（不是 single_agent.py / multi_agent.py 这种暴露实现细节的命名）
- 所有 agent 实现同一个 `Agent` 接口
- 单 agent / 多 agent 都可以独立用，也可以由 Router 自动选

## 架构

```
用户输入
   ↓
api (CLI / 未来可换 HTTP)
   ↓
orchestration/Router
   ↓ (返回 registry key)
orchestration/AgentRegistry
   ↓ (按 key 取 agent)
agents/QuickAssistant  或  agents/TravelPlanner
                              ↓
                         orchestration/Coordinator
                              ↓
                         多个 specialist agent
                              ↓
                            tools
```

## 项目结构
```
travel-agent/
├── main.py                      ← 组装入口
├── pyproject.toml
├── tests/
└── app/
    ├── api/                     ← 服务/接口层: FastAPI / WebSocket / CLI
    ├── orchestration/           ← 编排层: 核心。
    │   ├── router.py            ← 任务路由
    │   ├── registry.py          ← agent 注册表
    │   └── coordinator.py       ← 通用 multi-agent 协调器 (Supervisor 模式)
    ├── agents/                  ← agent 个体
    │   ├── base.py              ← Agent 抽象基类
    │   ├── runtime.py           ← SingleAgent 通用实现
    │   ├── quick_assistant.py   ← 简单查询 agent (当前 single, 可升级)
    │   ├── travel_planner.py    ← 复杂规划 agent (Coordinator + 专家)
    │   ├── flight_specialist.py
    │   ├── hotel_specialist.py
    │   ├── weather_specialist.py
    │   └── restaurant_specialist.py
    ├── tools/                   ← 工具层
    ├── models/                  ← 模型/Provider 层
    ├── memory/                  ← 记忆层
    ├── infrastructure/          ← 基础设施层
    ├── core/                    ← 公共类型
    └── config/                  ← 配置

```

### Agent / Multi-Agent 项目的典型分层架构

1. 基础设施层 (Infrastructure Layer)

负责最底层的资源和外部依赖，比如 LLM 调用、向量数据库、消息队列、日志等。
Python 里常见命名：
```
infrastructure/   或   infra/
├── llm/              # LLM 客户端封装 (openai, anthropic, etc.)
├── vector_store/     # 向量库 (chroma, qdrant, pinecone)
├── storage/          # 持久化 (redis, postgres, s3)
├── messaging/        # 消息总线 (kafka, rabbitmq, redis pub/sub)
└── observability/    # 日志、tracing、metrics
```

2. 模型/Provider 层 (Model Layer)
对不同 LLM provider 的统一抽象，方便切换模型。
```
models/   或   providers/
├── base.py           # BaseLLM 抽象类
├── anthropic_llm.py
├── openai_llm.py
└── embeddings.py
```

3. 工具层 (Tool Layer)
agent 能调用的能力，比如搜索、代码执行、API 调用、文件读写。
```
tools/
├── base.py           # BaseTool 抽象 (name, description, schema, run)
├── registry.py       # ToolRegistry，工具注册和查找
├── web_search.py
├── code_executor.py
├── file_tools.py
└── api_tools/
```

4. 记忆层 (Memory Layer)
短期对话记忆、长期记忆、知识库检索 (RAG)。
```
memory/
├── base.py
├── short_term.py     # ConversationBufferMemory 类
├── long_term.py      # 向量化长期记忆
├── episodic.py       # 事件记忆
└── retriever.py      # RAG 检索器
```

5. Agent 核心层 (Agent Core)
单个 agent 的大脑：规划、推理、工具调用循环 (ReAct / Plan-Execute / Reflexion 等)。
```
agents/
├── base_agent.py     # BaseAgent 抽象
├── react_agent.py
├── planner_agent.py
├── executor_agent.py
├── critic_agent.py
└── prompts/          # 各 agent 的 system prompt 模板
```

6. 编排层 (Orchestration Layer)
多 agent 协作的关键，决定谁先做、谁后做、怎么传消息。这是 multi-agent 项目最核心的一层。
```
orchestration/   或   workflows/
├── coordinator.py    # 总调度器 / Supervisor
├── router.py         # 路由决策 (哪个 agent 处理)
├── graph.py          # 如果用 langgraph 风格的状态图
├── state.py          # 共享状态 / Blackboard
└── communication.py  # agent 间消息协议
```

7. 服务/接口层 (Service / API Layer)
对外暴露的接口，FastAPI / WebSocket / CLI。
```
api/   或   server/
├── main.py           # FastAPI 入口
├── routes/
├── schemas/          # Pydantic 请求/响应模型
└── middlewares/
```

8. 配置与公共层
```
config/
├── settings.py       # Pydantic Settings
└── prompts.yaml

core/   或   common/
├── types.py          # 全局类型定义
├── exceptions.py
└── utils.py
```

#### 选型建议

如果是小项目 (单 agent + 几个工具)，可以把 agents/, tools/, memory/ 三层合到一个 core/ 里。
如果是 multi-agent 项目，编排层 (orchestration) 一定要独立出来，因为这是最容易复杂化、最值得抽象的地方。常见模式有 Supervisor (一个老板派活)、Hierarchical (老板下面还有小老板)、Network (peer to peer)、Blackboard (共享黑板)。

#### LLM 在 infra 层和 Models 层

- infra 层的 LLM 客户端：管"怎么跟外部 API 说话"，是技术细节
	- 封装 HTTP 调用，处理网络层的事
	- 处理HTTP、重试、超时、限流、连接池、错误处理、流式传输、token 计费埋点。
	比如`infrastructure/llm/anthropic_client.py`里 class 为 `AnthropicClient`

- Models 层的 LLM 抽象：管"在我的业务里 LLM 长什么样"，是领域接口
	- 是业务抽象
	- 关系统一的消息格式、tool calling 协议转换、不同 provider 的差异屏蔽、token 用量统计的语义层、温度/top_p 等业务参数
	
调用关系：
```
agents/                      业务层          
→  models/BaseLLM            业务抽象层  
→  infra/llm/openAIClient    技术封装层 
→  api.openAI.com            外部
                                             
```

## 安装和运行

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh  # 装 uv
uv sync                                           # 装依赖
cp .env.example .env                              # 配置 API key
uv run python main.py                             # 跑
```