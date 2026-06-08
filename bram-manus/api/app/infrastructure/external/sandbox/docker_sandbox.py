import asyncio
import logging
import socket
import uuid
from typing import Optional, Self

import docker
from async_lru import alru_cache
import httpx
from docker.models.resource import Model
from watchfiles import awatch

from app.domain.external.sandbox import Sandbox
from core.config import get_settings

logger = logging.getLogger(__name__)

class DockerSandbox(Sandbox):
    """基于Docker的沙箱服务"""

    def __init__(
            self,
            ip: Optional[str] = None,
            container_name: Optional[str] = None,
    ) -> None:
        """构造函数，完成沙箱扩展创建"""
        self.client = httpx.AsyncClient(timeout=600)
        self._ip = ip
        self._container_name = container_name
        self._base_url = f"http://{ip}:8080"
        self._vnc_url = f"ws://{ip}5901"
        self._cdp_url = f"http://{ip}:9222"

    @property
    def id(self) -> str:
        """获取沙箱唯一id（容器名字）"""
        if not self._container_name:
            return "bram-manus-sandbox"
        return self._container_name

    @property
    def vnc_url(self) -> str:
        return self._vnc_url

    @property
    def cdp_url(self) -> str:
        return self._cdp_url

    @classmethod
    @alru_cache(maxsize=128, typed=True) # 1和1.0不一样，就会更新缓存
    async def _resolve_hostname_to_ip(cls, hostname: str) -> Optional[str]:
        """将docker容器主机/地址转换成ipv4格式数据"""
        try:
            # 1.解析传递的hostname是不是ip
            try:
                # AF_INET ipv4
                socket.inet_pton(socket.AF_INET, hostname)
                return hostname
            except OSError:
                pass

            # 2.使用socket获取地址信息
            addr_info = socket.getaddrinfo(hostname, None, family=socket.AF_INET)

            if addr_info and len(addr_info) > 0:
                return addr_info[0][4][0]
            return None
        except Exception as e:
            logger.error(f"解析Docker容器主机地址{hostname}失败：{str(e)}")
            return None

    @classmethod
    def _get_container_ip(cls, container: Model) -> str:
        """根据传递的容器获取ip信息"""
        # 获取inspect
        network_settings = container.attrs["NetworkSettings"]
        ip_address = network_settings["IPAddress"]

        if not ip_address and "Networks" in network_settings:
            networks = network_settings["Networks"]
            for network_name, network_config in networks.items():
                if "IPAddress" in network_config and network_config["IPAddress"]:
                    ip_address = network_config["IPAddress"]
                    break

        return ip_address

    @classmethod
    def _create_task(cls) -> Self:
        """创建沙箱容器的异步任务"""
        settings = get_settings()

        image = settings.sandbox_image
        name_prefix = settings.sandbox_name_prefix
        container_name = f"{name_prefix}-{str(uuid.uuid4())[:8]}"

        try:
            # 创建docker客户端
            client = docker.from_env()

            container_config = {
                "image": image,
                "name": container_name,
                "detach": True,
                "remove": True,
                "environment": {
                    "SERVICE_TIMEOUT_MINUTES": settings.sandbox_ttl_minutes,
                    "CHROME_ARGS": settings.sandbox_chrome_args,
                    "HTTPS_PROXY": settings.sandbox_https_proxy,
                    "HTTP_PROXY": settings.sandbox_http_proxy,
                    "NO_PROXY": settings.sandbox_no_proxy,
                }
            }

            # 判断是否传递了网络
            if settings.sandbox_network:
                container_config["network"] = settings.sandbox_network

            # 调用docker客户端运行
            container = client.containers.run(**container_config)

            # 重载并刷新容器信息
            container.reload()
            ip = cls._get_container_ip(container)

            return DockerSandbox(ip=ip, container_name=container_name)
        except Exception as e:
            logger.error(f"创建Docker沙箱容器失败：{str(e)}")
            raise Exception(f"创建Docker沙箱容器失败：{str(e)}")

    @classmethod
    async def create(cls) -> Self:
        """类方法，创建沙箱容器"""
        settings = get_settings()

        # 判断是否使用现成的沙箱
        if settings.sandbox_address:
            ip = await cls._resolve_hostname_to_ip(settings.sandbox_address)
            return DockerSandbox(ip=ip)

        return await asyncio.to_thread(cls._create_task)
