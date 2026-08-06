import logging
from typing import List, AsyncGenerator

from fastapi import UploadFile
from pydantic import TypeAdapter

from app.domain.external.browser import Browser
from app.domain.external.file_storage import FileStorage
from app.domain.external.json_parser import JSONParser
from app.domain.external.llm import LLM
from app.domain.external.sandbox import Sandbox
from app.domain.external.search import SearchEngine
from app.domain.external.task import TaskRunner, Task
from app.domain.models.app_config import AgentConfig, MCPConfig, A2AConfig
from app.domain.models.event import ErrorEvent, Event, MessageEvent, BaseEvent, ToolEvent
from app.domain.models.file import File
from app.domain.models.message import Message
from app.domain.models.session import SessionStatus
from app.domain.repositories.file_repository import FileRepository
from app.domain.repositories.session_repository import SessionRepository
from app.domain.services.flows.planner_react import PlannerReactFlow
from app.domain.services.tools.a2a import A2ATool
from app.domain.services.tools.mcp import MCPTool

logger = logging.getLogger(__name__)
class AgentTaskRunner(TaskRunner):
    """基于Agent智能体的任务运行器"""

    def __init__(
            self,
            llm: LLM,
            agent_config: AgentConfig,
            mcp_config: MCPConfig,
            a2a_config: A2AConfig,
            session_id: str,
            session_repository: SessionRepository, # 会话仓库
            file_storage: FileStorage, # 文件存储桶
            file_repository: FileRepository, # 文件数据仓库
            json_parser: JSONParser,
            browser: Browser,
            search_engine: SearchEngine,
            sandbox: Sandbox
    ) -> None:
        """构造函数，完成Agent任务运行器的创建"""
        self._session_id = session_id
        self._session_repository = session_repository
        self._sandbox = sandbox
        self._mcp_config = mcp_config
        self._mcp_tool = MCPTool()
        self._a2a_config = a2a_config
        self._a2a_tool = A2ATool()
        self._file_storage = file_storage
        self._file_repository = file_repository
        self._browser = browser
        self._flow = PlannerReactFlow(
            llm=llm,
            agent_config=agent_config,
            session_id=session_id,
            session_repository=session_repository,
            json_parser=json_parser,
            browser=browser,
            sandbox=sandbox,
            search_engine=search_engine,
            mcp_tool=self._mcp_tool,
            a2a_tool=self._a2a_tool,
        )

    async def _put_and_add_event(self, task: Task, event: Event) -> None:
        """往指定任务的消息队列中添加事件"""
        event_id = await task.output_stream.put(event.model_dump_json())
        event.id = event_id

        await self._session_repository.add_event(self._session_id, event)

    @classmethod
    async def _pop_event(cls, task: Task) -> Event:
        """从任务的输入流中获取事件信息"""
        # 1.从任务的task中读取数据
        event_id, event_str = await task.input_stream.pop()
        if event_str is None:
            logger.warning(f"AgentTaskRunner接收到空消息")
            return

        # 2.使用pydantic+type类型将字符串转换成事件
        event = TypeAdapter(Event).validate_json(event_str)
        event.id = event_id

        # 这是写的什么
        return Event

    async def _sync_file_to_sandbox(self, file_id: str) -> File:
        """根据文件id将文件同步到沙箱中"""
        try:
            # 1.调用文件存储下载文件信息
            file_data, file = await self._file_storage.download_file(file_id)

            filepath = f"/home/ubuntu/upload/{file.filename}"

            tool_result = await self._sandbox.upload_file(
                file_data=file_data,
                filepath=filepath,
                filename=file.filename,
            )

            if tool_result.success:
                file.filepath = filepath
                await self._file_repository.save(file)
                return file

        except Exception as e:
            logger.exception(f"AgentTaskRunner同步文件[{file_id}]失败：{str(e)}")

    async def _sync_message_attachments_to_sandbox(self, event: MessageEvent) -> None:
        """将消息事件中的附件同步到沙箱中"""
        # 附件列表
        attachments: List[str] = []

        try:
            # 判断消息中是否存在附件
            if event.attachments:
                for attachment in event.attachments:
                    # 根据同步文件的id将数据同步到沙箱中
                    file = await self._sync_file_to_sandbox(attachment.id)

                    if file:
                        attachments.append(file)
                        await self._session_repository.add_file(self._session_id, file)
                event.attachments = attachments
        except Exception as e:
            logger.exception(f"AgentTaskRunner同步消息附件到沙箱失败：{str(e)}")

    # 没懂
    async def _sync_file_to_storage(self, filepath: str) -> File:
        """将沙箱中指定的文件路径数据同步到存储桶中"""
        try:
            # 根据文件路径从会话中查找文件数据
            file = await self._session_repository.get_file_by_path(filepath)

            # 从沙箱下载文件
            file_data = await self._sandbox.download_file(filepath)

            if file:
                await self._session_repository.remove_file(self._session_id, file.filepath)

            filename = filepath.split("/")[-1]
            upload_file = UploadFile(file=file_data, filename=filename)
            # todo:upload_file.content_type类型需要确认是否可以不填写

            file = await self._file_storage.upload_file(upload_file)
            file.filepath = filepath

            await self._session_repository.add_file(self._session_id, file)

        except Exception as e:
            logger.exception(f"AgentTaskRunner同步消息附件到文件存储桶失败：{str(e)}")


    async def _sync_message_attachments_to_storage(self, event: MessageEvent) -> None:
        """将消息事件的附件同步到文件存储桶中"""
        attachments: List[File] = []

        try:
            if event.attachments:
                for attachment in event.attachments:
                    file = await self._sync_file_to_storage(attachment.filepath)

                    if file:
                        attachments.append(file)
                        # 为什么没有这句
                        # await self._session_repository.add_file(self._session_id, file)
            event.attachments = attachments
        except Exception as e:
            logger.exception(f"AgentTaskRunner同步消息附件到存储桶失败：{str(e)}")


    async def _run_flow(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        """根据消息对象运行PlannerReActFlow"""
        if not message.message:
            logger.warning(f"AgentTaskRunner接收了一条空消息")
            yield ErrorEvent(error="空消息错误")
            return

        async for event in self._flow.invoke(message):
            # 判断是否tool，是则额外处理
            if isinstance(event, ToolEvent):
                # todo:工具事件额外处理
                pass
            elif isinstance(event, MessageEvent):
                # 如果是消息事件则将AI消息事件中的附件同步到存储中
                await self._sync_message_attachments_to_storage(event)

            yield event

    async def invoke(self, task: Task) -> None:
        """根据传递的任务处理agent消息队列并运行agent流"""
        try:
            # 1.确保沙箱、mcp、a2a均初始化完成
            logger.info(f"AgentTaskRunner任务处理开始")
            await self._sandbox.ensure_sandbox()
            await self._mcp_tool.initialize(self._mcp_config)
            await self._a2a_tool.initialize(self._a2a_config)

            # 2.循环读取任务中的输入消息队列
            while not await task.input_stream.is_empty():
                # 3.从输入流中获取数据
                event = await self._pop_event(task)
                message = ""

                # 4.判断事件类型是否为消息，是则处理消息并将消息附件同步到沙箱
                if isinstance(event, MessageEvent):
                    message = event.message or ""
                    await self._sync_message_attachments_to_sandbox(event)
                    logger.info(f"AgentTaskRunner接收到新消息：{message[:50]}...")

                # 消息事件转换成消息对象
                message_obj = Message(
                    message=message,
                    attachments=[attachment.filepath for attachment in event.attachments],
                )

                async for event in self._run_flow(message_obj):
                    pass

        except Exception as e:
            logger.exception(f"AgentTaskRunner运行出错：{str(e)}")
            await self._put_and_add_event(task, ErrorEvent(error=f"AgentTaskRunner出错"))
            await self._session_repository.update_status(self._session_id, SessionStatus.COMPLETED)

    async def destroy(self) -> None:
        """销毁任务并释放资源"""
        logger.info(f"开始清除销毁AgentTaskRunner资源")
        if self._sandbox:
            logger.info(f"开始清除销毁AgentTaskRunner中的沙箱环境")
            await self._sandbox.destroy()

        if self._mcp_tool:
            logger.info(f"开始清除销毁AgentTaskRunner中的mcp工具")
            await self._mcp_tool.cleanup()

        if self._a2a_tool:
            logger.info(f"开始清除销毁AgentTaskRunner中的a2a工具")
            await self._a2a_tool.manager.cleanup()


    async def on_done(self, task: Task) -> None:
        """任务结束时执行的回调函数"""
        logger.info(f"AgentTaskRunner任务执行结束")

