from datetime import datetime as dt

from sqlalchemy import String, ForeignKey, Integer, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.models.user import User


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    author_id: Mapped[str] = mapped_column(String(40), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(55), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[dt] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[dt] = mapped_column(DateTime, server_default=func.now())

    author: Mapped["User"] = relationship()
    