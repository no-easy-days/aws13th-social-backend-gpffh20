from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.commons import Content, CommentId, Pagination, PostId, UserId


class CommentCreateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    content: Content


class CommentItemBase(BaseModel):
    """댓글 기본 필드"""
    model_config = ConfigDict(from_attributes=True)

    id: CommentId
    post_id: PostId
    author_id: UserId | None
    content: Content
    created_at: datetime


class CommentListItem(CommentItemBase):
    """게시글 댓글 목록용 (author_nickname 포함)"""
    author_nickname: str | None


MyCommentListItem = CommentItemBase


class CommentUpdateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    content: Content


class CommentListResponse(BaseModel):
    """게시글 댓글 목록 응답"""
    data: list[CommentListItem]
    pagination: Pagination


class MyCommentListResponse(BaseModel):
    """내 댓글 목록 응답"""
    data: list[MyCommentListItem]
    pagination: Pagination
