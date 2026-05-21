from typing import Optional, List

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """搜索结果条目数据类型"""
    url: str
    title: str
    snippet: str = ""  # 搜索条目摘要


class SearchResults(BaseModel):
    """搜索结果数据模型"""
    query: str
    date_range: Optional[str]
    total_results: int = 0  # 搜索结果数
    results: List[SearchResultItem] = Field(default_factory=list)  # 搜索结果
