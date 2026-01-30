from datetime import datetime

from sqlalchemy import String, ForeignKey, Integer, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.models.user import User
    from db.models.post import Post


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    author_id: Mapped[str | None] = mapped_column(String(40), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    post_id: Mapped[str] = mapped_column(String(40), ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    author: Mapped["User | None"] = relationship(back_populates="comments", lazy="noload")
    post: Mapped["Post"] = relationship(back_populates="comments", lazy="noload")

    @property
    def author_nickname(self) -> str | None:
        return self.author.nickname if self.author else None
