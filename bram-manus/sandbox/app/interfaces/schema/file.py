from typing import Optional

from pydantic import BaseModel, Field


class ReadFileResult(BaseModel):
    """读取文件请求结构体"""
    filepath: str = Field(..., description="要读取文件的绝对路径")
    start_line: Optional[int] = Field(default=None, description="(可选)读取的起始行，索引从0开始")
    end_line: Optional[int] = Field(default=None, description="(可选)读取的结束行，不包含该行")
    sudo: Optional[bool] = Field(default=False, description="(可选)是否使用sudo权限")
    max_length: Optional[int] = Field(default=10000, description="(可选)要返回的内容的最大长度")
