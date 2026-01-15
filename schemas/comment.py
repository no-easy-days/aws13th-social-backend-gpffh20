from datetime import datetime

from pydantic import BaseModel, model_validator

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
    content: Content | None = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.content is None:
            raise ValueError("수정할 필드가 없습니다.")
        return self


class CommentUpdateResponse(CommentBase):
    updated_at: datetime


class CommentListResponse(BaseModel):
    data: list[CommentBase]
    pagination: Pagination
