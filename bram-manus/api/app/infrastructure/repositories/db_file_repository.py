from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.file import File
from app.domain.repositories.file_repository import FileRepository
from app.infrastructure.models import FileModel


class DBFileRepository(FileRepository):
    """基于数据库的文件数据仓库"""

    def __init__(self, db_session: AsyncSession) -> None:
        """构造函数，完成数据仓库初始化"""
        self.db_session = db_session

    async def save(self, file: File) -> None:
        """根据传递的文件模型存储or更新数据"""
        statement = select(FileModel).where(FileModel.id == file.id)
        result = await self.db_session.execute(statement)
        record = result.scalar_one_or_none()

        if not record:
            record = FileModel.from_domain(file)
            self.db_session.add(record)
            return

        record.update_from_domain(file)

    async def get_by_id(self, file_id: str) -> Optional[File]:
        """根据传递的文件id获取文件信息"""
        statement = select(FileModel).where(FileModel.id == file_id)
        result = await self.db_session.execute(statement)
        record = result.scalar_one_or_none()

        return record.to_domain() if record is not None else None