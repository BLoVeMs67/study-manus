from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.session import Session, SessionStatus
from app.domain.repositories.session_repository import SessionRepository
from app.infrastructure.models import SessionModel


class DBSessionRepository(SessionRepository):
    """基于Postgres数据库的会话仓库"""

    def __init__(self, db_session: AsyncSession) -> None:
        """构造函数，数据库初始化"""
        self.db_session = db_session

    async def save(self, session: Session) -> None:
        # 1.根据id查询会话是否存在
        statement = select(SessionModel).where(SessionModel.id == session.id)
        result = await self.db_session.execute(statement)
        record = result.scalar_one_or_none()

        if not record:
            record = SessionModel.from_domain(session)
            self.db_session.add(record)
            return

        record.update_from_domain(session)

    async def get_all(self) -> List[Session]:
        """获取所有会话列表"""
        # SELECT * FROM sessions ORDER BY latest_message_at DESC; 倒序
        statement = select(SessionModel).order_by(SessionModel.latest_message_at.desc())
        result = await self.db_session.execute(statement)
        records = result.scalars().all()

        return [record.to_domain() for record in records]

    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """根据会话id获取会话数据"""
        statement = select(SessionModel).where(SessionModel.id == session_id)
        result = await self.db_session.execute(statement)
        record = result.scalar_one_or_none()

        if not record:
            return None

        return record.to_domain()

    async def delete_by_id(self, session_id: str) -> None:
        """根据会话id删除会话"""
        statement = delete(SessionModel).where(SessionModel.id == session_id)
        await self.db_session.execute(statement)

    async def update_title(self, session_id: str, title: str) -> None:
        """更新会话标题"""
        statement = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(title=title)
        )
        result = await self.db_session.execute(statement)

        if result.rowcount == 0:
            raise ValueError(f"会话[{session_id}]不存在，请核实后重试")

    async def update_latest_message(self, session_id: str, message: str, timestamp: datetime) -> None:
        """更新会话最新消息"""
        statement = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(
                latest_message_at=timestamp,
                latest_message=message
            )
        )
        result = await self.db_session.execute(statement)

        if result.rowcount == 0:
            raise ValueError(f"会话[{session_id}]不存在，请核实后重试")

    async def update_status(self, session_id: str, status: SessionStatus) -> None:
        """更新会话状态"""
        statement = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(status=status.value) # 因为status是枚举
        )
        result = await self.db_session.execute(statement)

        if result.rowcount == 0:
            raise ValueError(f"会话[{session_id}]不存在，请核实后重试")

    async def update_unread_message_count(self, session_id: str, count: int) -> None:
        """更新会话的未读消息数"""
        statement = (
            update(SessionModel)
            .where(SessionModel.id == session_id)
            .values(unread_message_count=count)
        )
        result = await self.db_session.execute(statement)

        if result.rowcount == 0:
            raise ValueError(f"会话[{session_id}]不存在，请核实后重试")