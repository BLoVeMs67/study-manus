import asyncio
import io
import logging
import uuid
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
from app.domain.models.event import ErrorEvent, Event, MessageEvent, BaseEvent, ToolEvent, ToolEventStatus, \
    BrowserToolContent, SearchToolContent, ShellToolContent, FileToolContent, MCPToolContent, A2AToolContent, \
    TitleEvent, WaitEvent, DoneEvent
from app.domain.models.file import File
from app.domain.models.message import Message
from app.domain.models.search import SearchResults
from app.domain.models.session import SessionStatus
from app.domain.models.tool_result import ToolResult
from app.domain.repositories.file_repository import FileRepository
from app.domain.repositories.session_repository import SessionRepository
from app.domain.services.flows.planner_react import PlannerReactFlow
from app.domain.services.tools.a2a import A2ATool
from app.domain.services.tools.mcp import MCPTool
from core.config import get_settings

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

    async def _get_browser_screenshot(self) -> str:
        """获取浏览器截图并返回截图文件对应的在线URL"""
        # 1.调用浏览器完成截图
        screenshot = await self._browser.screenshot()

        # 2.将浏览器截图上传到文件存储中
        file = await self._file_storage.upload_file(UploadFile(
            file=io.BytesIO(screenshot),
            filename=f"{str(uuid.uuid4())}.png",
            # # bugfix:添加size尺寸
            # size=self._get_stream_size(io.BytesIO(screenshot)),
        ))

        # # 3.获取setting并组装完整URL
        # settings = get_settings()
        # return f"https://{settings.cos_bucket}.cos.{settings.cos_region}.myqcloud.com/{file.key}"

        return file.id

    async def _handle_tool_event(self, event: ToolEvent) -> None:
        """额外处理工具消息，使其前端交互更友好"""
        try:
            # 1.如果事件状态为已调用则执行以下代码
            if event.status == ToolEventStatus.CALLED:
                # 2.工具为浏览器则补全工具浏览器工具内容
                if event.tool_name == "browser":
                    event.tool_content = BrowserToolContent(
                        screenshot=await self._get_browser_screenshot(),
                    )
                elif event.tool_name == "search":
                    # 3.工具为搜索则添加搜索工具内容
                    search_results: ToolResult[SearchResults] = event.function_result
                    logger.info(f"搜索工具结果: {search_results}")
                    event.tool_content = SearchToolContent(results=search_results.data.results)
                elif event.tool_name == "shell":
                    # 4.工具为shell则生成shell工具内容
                    if "session_id" in event.function_args:
                        shell_result = await self._sandbox.read_shell_output(
                            event.function_args["session_id"],
                            console=True,
                        )
                        event.tool_content = ShellToolContent(
                            console=(shell_result.data or {}).get("console_records", [])
                        )
                    else:
                        event.tool_content = ShellToolContent(console="(No console)")
                elif event.tool_name == "file":
                    # 5.工具为file则将文件同步到对象存储
                    if "filepath" in event.function_args:
                        filepath = event.function_args["filepath"]
                        file_read_result = await self._sandbox.read_file(filepath)
                        file_content: str = (file_read_result.data or {}).get("content", "")
                        event.tool_content = FileToolContent(content=file_content)
                        # bugfix:修改为同步文件到storage
                        await self._sync_file_to_storage(filepath)
                    else:
                        event.tool_content = FileToolContent(content="(No Content)")
                elif event.tool_name in ["mcp", "a2a"]:
                    # 6.工具为mcp/a2a则处理调用结果
                    logger.info(f"处理MCP/A2A工具事件, function_result: {event.function_result}")
                    if event.function_result:
                        # 7.如果结果包含data则提取data
                        if hasattr(event.function_result, "data") and event.function_result.data:
                            logger.info(f"MCP/A2A工具调用结果: {event.function_result.data}")
                            event.tool_content = MCPToolContent(result=event.function_result.data) \
                                if event.tool_name == "mcp" \
                                else A2AToolContent(a2a_result=event.function_result.data)
                        elif hasattr(event.function_result, "success") and event.function_result.success:
                            # 8.mcp/a2a工具调用正常，但是无结果产生
                            logger.info(f"MCP/A2A工具调用成功返回，但无结果: {event.function_result}")
                            result_data = event.function_result.model_dump() \
                                if hasattr(event.function_result, "model_dump") \
                                else str(event.function_result)
                            event.tool_content = MCPToolContent(result=result_data) \
                                if event.tool_name == "mcp" \
                                else A2AToolContent(a2a_result=result_data)
                        else:
                            # 9.其他情况将结果转换成字符串进行传递
                            logger.info(f"MCP/A2A工具额记过: {event.function_result}")
                            event.tool_content = MCPToolContent(result=str(event.function_result)) \
                                if event.tool_name == "mcp" \
                                else A2AToolContent(a2a_result=str(event.function_result))
                    else:
                        logger.warning("MCP/A2A工具调用结果未发现")
                        event.tool_content = MCPToolContent(result="(MCP工具无可用结果)") \
                            if event.tool_name == "mcp" \
                            else A2AToolContent(a2a_result="(A2A智能体无可用结果)")
        except Exception as e:
            logger.exception(f"AgentTaskRunner生成工具内容失败: {str(e)}")

    async def _run_flow(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        """根据消息对象运行PlannerReActFlow"""
        if not message.message:
            logger.warning(f"AgentTaskRunner接收了一条空消息")
            yield ErrorEvent(error="空消息错误")
            return

        async for event in self._flow.invoke(message):
            # 判断是否tool，是则额外处理
            if isinstance(event, ToolEvent):
                await self._handle_tool_event(event)
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
                    await self._put_and_add_event(task, event)

                    if isinstance(event, TitleEvent):
                        await self._session_repository.update_title(self._session_id, event.title)
                    elif isinstance(event, MessageEvent):
                        await self._session_repository.update_latest_message(
                            self._session_id,
                            event.message,
                            event.created_at
                        )
                        await self._session_repository.increment_unread_message_count(self._session_id)
                    elif isinstance(event, WaitEvent):
                        await self._session_repository.update_status(self._session_id, SessionStatus.WAITING)
                        return

                # 若输入消息队列为空，则跳出循环
                if not await task.input_stream.is_empty():
                    break

            # 12.更新会话状态为已完成

            await self._session_repository.update_status(self._session_id, SessionStatus.COMPLETED)
        except asyncio.CancelledError:
            # 13.异步任务被取消，推送结束事件并跟新状态
            logger.info(f"AgentTaskRunner任务运行取消")
            await self._put_and_add_event(task, DoneEvent())
            await self._session_repository.update_status(self._session_id, SessionStatus.COMPLETED)
            raise
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

