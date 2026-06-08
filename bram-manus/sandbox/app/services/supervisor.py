"""
1.Supervisor启动后，通过一个Unix套接字文件来实现通信(rpc协议)
2.连接这个通信文件，/tmp/supervisor.sock ((python库)xml-rpc连接)
3.使用某种方式来完整转换，让xml-rpc实现连接supervisor.sock
4.连接之后我们就可以调用rpc对应的方法，getAllProcessInfo()
"""
import asyncio
import datetime
import http.client
import logging
import socket
import threading
import xmlrpc
import xmlrpc.client
from datetime import timedelta
from typing import Optional, List, Any

from app.core.config import get_settings
from app.interfaces.errors.exceptions import BadRequestException, AppException
from app.models.supervisor import ProcessInfo, SupervisorActionResult

logger = logging.getLogger(__name__)


class UnixStreamHTTPConnection(http.client.HTTPConnection):
    """基于Unix流的HTTP连接处理器"""

    def __init__(self, host: str, socket_path: str, timeout: Optional[int] = None) -> None:
        """构造函数，完成连接器初始化"""
        http.client.HTTPConnection.__init__(self, host, timeout)
        self.socket_path = socket_path

    def connect(self) -> None:
        """重写连接方法，欺骗xml-rpc库让其觉得自己正在进行网络连接"""
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


class UnixStreamTransport(xmlrpc.client.Transport):
    """基于Unix流传输层的适配器/转换器"""

    def __init__(self, socket_path: str) -> None:
        """构造函数，完成传输适配器的初始化"""
        xmlrpc.client.Transport.__init__(self)
        self.socket_path = socket_path

    def make_connection(self, host) -> http.client.HTTPConnection:
        return UnixStreamHTTPConnection(host, self.socket_path)


class SupervisorService():
    """Supervisor服务"""

    def __init__(self) -> None:
        """构造函数,完成supervisor服务链接"""
        # 1.连接supervisor配置
        self.rpc_url = "/tmp/supervisor.sock"
        self._connect_rpc()

        # 2.supervisor超时配置
        settings = get_settings()
        self.timeout_active = settings.server_timeout_minutes is not None
        self.shutdown_task = None
        self.shutdown_timer = None
        self._expand_enabled = True  # 是否自动保活（每调用一次接口就增加时间）

        # 3.检测是否配置了自动销毁
        if settings.server_timeout_minutes is not None:
            # 4.设置销毁时间+定时器
            self.shutdown_timer = datetime.now() + timedelta(minutes=settings.server_timeout_minutes)
            self._setup_timer(settings.server_timeout_minutes)

    @property
    def expand_enabled(self) -> bool:
        """只读，返回是否自动保活"""
        return self._expand_enabled

    def enable_expand(self) -> None:
        """开启自动保活"""
        self._expand_enabled = True

    def disable_expand(self) -> None:
        """关闭自动保活"""
        self._expand_enabled = False

    def _setup_timer(self, minutes: int) -> None:
        """传递时间（分钟）并创建定时器，在时间结束后关闭supervisor主进程"""
        # 1.检测当前是否存在销毁任务，如果存在则先取消
        if self.shutdown_task:
            try:
                self.shutdown_task.cancel()
            except Exception as e:
                logger.warning(f"取消shutdown任务失败：{str(e)}")

        # 2.创建一个新任务
        async def shutdown_after_timeout():
            await asyncio.sleep(minutes * 60)
            await self.shutdown()

        try:
            # 3.获取事件循环并添加任务
            loop = asyncio.get_event_loop()
            self.shutdown_task = loop.create_task(shutdown_after_timeout())
        except Exception as e:
            # 4.如果事件循环失败则创建一个新的线程来执行定时器
            if hasattr(self, "shutdown_timer") and self.shutdown_timer:
                self.shutdown_timer.cancel()

            # 5.使用线程创建关闭定时器并设置在后台运行
            self.shutdown_timer = threading.Timer(
                minutes * 60,
                lambda: asyncio.run(self.shutdown())
            )

            self.shutdown_timer.daemon = True
            self.shutdown_timer.start()

    def _connect_rpc(self) -> None:
        """使用python的xml-rpc客户端连接一个本地sock文件实现连接rpc服务"""
        try:
            self.server = xmlrpc.client.ServerProxy(
                "http://localhost",
                transport=UnixStreamTransport(self.rpc_url)
            )
        except Exception as e:
            logger.error(f"连接Supervisor服务失败：{str(e)}")
            raise BadRequestException(f"连接Supervisor服务失败：{str(e)}")

    @classmethod
    async def _call_rpc(cls, method, *args) -> Any:
        """根据传递的方法+参数调用rpc方法"""
        try:
            return await asyncio.to_thread(method, *args)
        except Exception as e:
            logger.error(f"RPC方法调用失败：{str(e)}")
            raise BadRequestException(f"RPC方法调用失败：{str(e)}")

    async def get_all_processes(self) -> List[ProcessInfo]:
        """获取当前supervisor管理的所有进程信息"""
        try:
            processes = await self._call_rpc(self.server.supervisor.getAllProcessInfo)
            return [ProcessInfo(**process) for process in processes]
        except Exception as e:
            logger.error(f"获取进程信息失败：{str(e)}")
            raise AppException(f"获取进程信息失败：{str(e)}")

    async def stop_all_processes(self) -> SupervisorActionResult:
        """停止所有supervisor进程服务"""
        try:
            result = await self._call_rpc(self.server.supervisor.stopAllProcesses)
            return SupervisorActionResult(status="stopped", result=result)
        except Exception as e:
            logger.error(f"停止所有supervisor进程服务失败：{str(e)}")
            raise AppException(f"停止所有supervisor进程服务失败：{str(e)}")

    async def shutdown(self) -> SupervisorActionResult:
        """关闭Supervisor服务"""
        try:
            shutdown_result = await self._call_rpc(self.server.supervisor.shutdown)
            return SupervisorActionResult(status="shutdown", shutdown_result=shutdown_result)
        except Exception as e:
            logger.error(f"关闭Supervisor服务失败：{str(e)}")
            raise AppException(f"关闭Supervisor服务失败：{str(e)}")

    async def restart(self) -> SupervisorActionResult:
        """重启Supervisor服务管理的进程"""
        try:
            stop_result = await self._call_rpc(self.server.supervisor.stopAllProcesses)
            start_result = await self._call_rpc(self.server.supervisor.startAllProcesses)
            return SupervisorActionResult(
                status="restart",
                stop_result=stop_result,
                start_result=start_result
            )
        except Exception as e:
            logger.error(f"重启Supervisor进程服务失败：{str(e)}")
            raise AppException(f"重启Supervisor进程服务失败：{str(e)}")
