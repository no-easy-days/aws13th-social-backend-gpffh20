from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.commons import Content, CommentId, Pagination, PostId, UserId


class CommentCreateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    content: Content


class CommentBase(BaseModel):
    """댓글 생성/조회에서 공통으로 쓰는 필드"""
    model_config = ConfigDict(from_attributes=True)

    id: CommentId
    post_id: PostId
    author_id: UserId
    content: Content
    created_at: datetime


class CommentUpdateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    content: Content


# CommentUpdateResponse = CommentBase


class CommentListResponse(BaseModel):
    data: list[CommentBase]
    pagination: Pagination
