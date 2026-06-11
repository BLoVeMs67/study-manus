import logging
import uuid
from contextlib import AsyncExitStack
from typing import Optional, Dict, Any

import httpx

from app.application.errors.exceptions import ServerRequestsError
from app.domain.models.app_config import A2AConfig
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

"""
A2A客户端管理器的开发思路:
1.在Agent执行过程中, 有可能需要多次调用Remote-Agent，
  但是a2a中的agent-card.json请求是网络io, 相对耗时，
  所以需要缓存agent-card的相关信息, 只有在初始化A2A客户端的时候才初始化一次,
  更新a2a服务器的时候更新, 清除a2a客户端管理器时删除;
2.在前端UI交互中, 无论A2A服务器是否启动, 都会展示Card信息,
  但是呢, 在执行/规划Agent中, 我们只传递启用的A2A服务, 所以A2A客户端管理器必须动态接受配置;
3.一个A2A客户端会同时管理多个Agent, 但是不同的A2A服务有可能他们的name是一样的，
  需要考虑传递给Agent信息时的唯一性, 会配置多一个唯一的id;
4.由于使用httpx客户端, 这个客户端需要创建上下文/释放资源, 所以可以使用AsyncExitStack来管理
  异步上下文, 避免大量使用with..as的嵌套组合;
5.A2AClientManager的初始化非常耗时, 一次请求中只初始化一次;
6.A2A配置是写在config.yaml中的并直接暴露给开发者, 有可能开发者会手动修改config.yaml
  所以在使用的时候, 最多需要做多一次校验;
7.A2A客户端管理器只实现两个方法, 一个是get_remote_agent_cards、call_remote_agent;
8.A2A客户端管理器停止时必须清除对应资源, 涵盖了缓存, 异步上下文管理器避免资源泄露;
"""

class A2AClientManager:
    """A2A客户端管理器"""

    def __init__(self, a2a_config: Optional[A2AConfig] = None) -> None:
        self._a2a_config = a2a_config
        self._exit_stack: AsyncExitStack = AsyncExitStack() # 上下文管理器
        self._httpx_client: Optional[httpx.AsyncClient] = None # httpx客户端
        self._agent_cards: Dict[str, Any] = {}
        self._initialized: bool = False

    @property
    def agent_cards(self) -> Dict[str, Any]:
        return self._agent_cards

    async def initialize(self) -> None:
        if self._initialized:
            return

        try:
            self._httpx_client = await self._exit_stack.enter_async_context(
                httpx.AsyncClient(timeout=600)
            )

            logger.info(f"加载{len(self._a2a_config.a2a_servers)}个A2A服务")
            await self._get_a2a_agent_cards()
            self._initialized = True
            logger.info(f"A2A客户端加载成功")
        except Exception as e:
            logger.error(f"A2A客户端管理器加载失败")
            raise ServerRequestsError(f"A2A客户端管理器加载失败")

    async def _get_a2a_agent_cards(self) -> None:
        """根据配置连接所有a2a服务器获取AgentCard配置"""
        for a2a_server_config in self._a2a_config.a2a_servers:
            try:
                agent_card_response = await self._httpx_client.get(
                    f"{a2a_server_config.base_url}/.well-known/agent-card.json"
                )
                agent_card_response.raise_for_status()
                agent_card = agent_card_response.json()

                self._agent_cards[a2a_server_config.id] = agent_card
            except Exception as e:
                logger.warning(f"加载A2A服务[{a2a_server_config.id}]失败：{str(e)}")
                continue

    async def invoke(self, agent_id: str, query: str) -> ToolResult:
        """根据传递的智能体id+query调用Remote-Agent"""
        if agent_id not in self._agent_cards:
            return ToolResult(success=False, message="该远程Agent不存在")

        agent_card = self._agent_cards.get(agent_id, {})
        # 肯定有问题
        url = agent_card.get("url", "")

        if url == "":
            return ToolResult(success=False, message="该远程Agent调用端点不存在")

        try:
            agent_response = await self._httpx_client.post(
                url,
                json={
                    "id": str(uuid.uuid4()),
                    "jsonrpc": "2.0",
                    "method": "SendMessage",
                    "params": {
                        "message": {
                            "messageId": uuid.uuid4().hex,
                            "role": "ROLE_USER",
                            "parts": [
                                {"text": query}
                            ]
                        }
                    }
                }
            )
            agent_response.raise_for_status()
            result = agent_response.json()

            return ToolResult(success=True, message="调用远程Agent成功", data=result)
        except Exception as e:
            logger.error(f"调用远程Agent[{agent_id}:{url}]出错：{str(e)}")
            return ToolResult(
                success=False,
                message=f"调用远程Agent[{agent_id}:{url}]出错：{str(e)}"
            )

    async def cleanup(self) -> None:
        """当退出A2A客户端管理器时，清除对应资源"""
        try:
            await self._exit_stack.aclose()
            self._agent_cards.clear()
            self._initialized = False
            logger.info(f"清除A2A客户端管理器成功")
        except Exception as e:
            logger.error(f"清理A2A客户端管理器失败：{str(e)}")