import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes, create_rest_routes
from fastapi import FastAPI
from mcp.shared.experimental.tasks.in_memory_task_store import InMemoryTaskStore
from a2a.types import AgentSkill, AgentCard, AgentCapabilities, AgentInterface
from agent_executor import DeepSeekAgentExecutor
from a2a.server.routes.fastapi_routes import add_a2a_routes_to_fastapi

# 成功运行后访问http://127.0.0.1:9999/.well-known/agent-card.json，可见
"""
{
  "name": "DeepSeek智能体",
  "description": "这是一个可以调用DeepSeek模型进行深度思考的智能体，在需要深度思考时可以使用",
  "supportedInterfaces": [
    {
      "url": "http://localhost:9999",
      "protocolBinding": "JSONRPC"
    }
  ],
  "version": "1.0.0",
  "capabilities": {
    "streaming": false
  },
  "defaultInputModes": [
    "text"
  ],
  "defaultOutputModes": [
    "text"
  ],
  "skills": [
    {
      "id": "calculator",
      "name": "计算器",
      "description": "支持计算各种复杂数学公式",
      "tags": [
        "计算器"
      ],
      "examples": [
        "445*34",
        "211/34.2+12"
      ]
    }
  ],
  "preferredTransport": "JSONRPC",
  "protocolVersion": "0.3",
  "url": "http://localhost:9999"
}
"""

if __name__ == "__main__":
    # 技能
    skill = AgentSkill(
        id="calculator",
        name="计算器",
        description="支持计算各种复杂数学公式",
        tags=["计算器"],
        examples=["445*34", "211/34.2+12"]
    )

    # 卡片
    agent_card = AgentCard(
        name="DeepSeek智能体",
        description="这是一个可以调用DeepSeek模型进行深度思考的智能体，在需要深度思考时可以使用",
        #url="http://localhost:9999",
        supported_interfaces=[AgentInterface(
            url="http://localhost:9999",
            protocol_binding="JSONRPC"
        )],
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[skill],
    )

    # 使用a2a默认的处理器（jsonrpc）
    request_handler = DefaultRequestHandler(
        agent_executor=DeepSeekAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )

    # # a2a服务器
    # server = A2AStarletteApplication(
    #     agent_card=agent_card,
    #     request_handler=request_handler,
    # )
    # uvicorn.run(server.build(), host="0.0.0.0", port=9999)

    app = FastAPI()

    # 获取路由列表
    agent_card_routes = create_agent_card_routes(agent_card)
    jsonrpc_routes = create_jsonrpc_routes(request_handler, '/')
    rest_routes = create_rest_routes(request_handler)

    # 使用 add_a2a_routes_to_fastapi 挂载路由
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=agent_card_routes,
        jsonrpc_routes=jsonrpc_routes,
        rest_routes=rest_routes,
    )
    uvicorn.run(app, host="0.0.0.0", port=9999)