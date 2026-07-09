import logging
from typing import AsyncGenerator, Optional

from .base import BaseFlow, FlowStatus
from app.domain.models.event import BaseEvent
from app.domain.models.message import Message
from app.domain.repositories.session_repository import SessionRepository
from app.domain.models.plan import Plan
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.file import FileTool
from app.domain.services.tools.shell import ShellTool
from app.domain.services.tools.browser import BrowserTool
from app.domain.external.browser import Browser
from app.domain.services.tools.search import SearchTool
from app.domain.external.search import SearchEngine
from app.domain.services.agents.planner import PlannerAgent
from app.domain.services.agents.react import ReActAgent
from app.domain.services.tools.a2a import A2ATool
from app.domain.services.tools.mcp import MCPTool
from app.domain.services.tools.message import MessageTool
from app.domain.external.json_parser import JSONParser
from app.domain.external.llm import LLM
from app.domain.models.app_config import AgentConfig


logger = logging.getLogger(__name__)

class PlannerReactFlow(BaseFlow):
    """规划与执行流"""

    def __init__(
            self,
            llm: LLM,
            agent_config: AgentConfig,
            session_id: str,
            session_repository: SessionRepository,
            json_parser: JSONParser,
            browser: Browser,
            sandbox: Sandbox,
            search_engine: SearchEngine,
            mcp_tool: MCPTool,
            a2a_tool: A2ATool,
    ) -> None:
        """构造函数，完成规划与执行流的初始化"""
        # 1.流初始化数据配置
        self._session_id = session_id
        self._session_repository = session_repository
        self.status = FlowStatus.IDLE
        self.plan: Optional[Plan] = None

        # 2.工具列表初始化
        tools = [
            FileTool(sandbox=sandbox),
            ShellTool(sandbox=sandbox),
            BrowserTool(browser=browser),
            SearchTool(search_engine=search_engine),
            MessageTool(),
            mcp_tool,
            a2a_tool
        ]

        # 3.创建规划agent
        self.planner = PlannerAgent(
            session_id=session_id,
            session_repository=session_repository,
            agent_config=agent_config,
            llm=llm,
            json_parser=json_parser,
            tools=tools,
        )
        logger.debug(f"创建规划Agent成功，会话id:{self._session_id}")
        # 4.创建执行Agent
        self.react = ReActAgent(
            session_id=session_id,
            session_repository=session_repository,
            agent_config=agent_config,
            llm=llm,
            json_parser=json_parser,
            tools=tools,
        )
        logger.debug(f"创建执行Agent成功，会话id:{self._session_id}")


    async def invoke(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        pass

    @property
    def done(self) -> bool:
        """只读，返回流是否运行结束"""
        return self.status == FlowStatus.IDLE