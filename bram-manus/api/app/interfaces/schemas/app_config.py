from typing import List

from pydantic import BaseModel, Field

from app.domain.models.app_config import MCPTransport


class ListMCPServerItem(BaseModel):
    """MCP服务列表条目选项"""
    server_name: str = ""  # 服务名字
    enabled: bool = True  # 启用状态
    transport: MCPTransport = MCPTransport.STREAMABLE_HTTP  # 传输协议
    tools: List[str] = Field(default_factory=list)  # 工具名字列表


class ListMCPServerResponse(BaseModel):
    """获取MCP服务列表响应结构"""
    mcp_servers: List[ListMCPServerItem] = Field(default_factory=list)


class ListA2AServerItem(BaseModel):
    """A2A服务列表条目选项"""
    id: str = ""
    name: str = ""
    description: str = ""
    input_modes: List[str] = Field(default_factory=list) # 输入模态
    output_modes: List[str] = Field(default_factory=list)
    streaming: bool = False
    push_notifications: bool = False # 是否支持推送通知
    enabled: bool = True # 启用状态


class ListA2AServerResponse(BaseModel):
    """获取A2A服务列表响应结构"""
    a2a_servers: List[ListA2AServerItem] = Field(default_factory=list)
