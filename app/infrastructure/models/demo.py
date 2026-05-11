import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    String,
    Text,
    DateTime,
    text,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Demo(Base):
    """Demo模型，用于演示alembic数据库迁移"""
    __tablename__ = "demos"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_demos_id"),
    )
    # 前面的UUID是python中的，后面的是数据库表中的
    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        nullable=False,
        primary_key=True,
        server_default=text('uuid_generate_v4()')
    )  # demo id
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )
    avatar: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        server_default=text("''::character varying")
    )  # 头像
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("''::text")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)'),
        onupdate=datetime.now,
    )  # 更新时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP(0)')
    )  # 创建时间
