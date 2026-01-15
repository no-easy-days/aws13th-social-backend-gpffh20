from datetime import datetime

from pydantic import BaseModel

from schemas.commons import Content, CommentId, Pagination, PostId, UserId


class CommentCreateRequest(BaseModel):
    content: Content


class CommentBase(BaseModel):
    """댓글 생성/조회에서 공통으로 쓰는 필드"""
    id: CommentId
    post_id: PostId
    author: UserId
    content: Content
    created_at: datetime


class CommentUpdateRequest(BaseModel):
    content: Content


class CommentUpdateResponse(CommentBase):
    updated_at: datetime


class CommentListResponse(BaseModel):
    data: list[CommentBase]
    pagination: Pagination
