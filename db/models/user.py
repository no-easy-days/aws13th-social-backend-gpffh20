from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.models.post import Post
    from db.models.comment import Comment

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(15), nullable=False)
    profile_img: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    posts: Mapped[list["Post"]] = relationship(back_populates="author", lazy="selectin")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author", lazy="selectin")
