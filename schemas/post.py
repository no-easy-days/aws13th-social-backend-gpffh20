from datetime import datetime
from typing import Annotated, Literal

from pydantic import StringConstraints, BaseModel, Field, model_validator

from schemas.commons import PostId, UserId, Pagination, Page, Content, Title, Count


class PostListItem(BaseModel):
    id: PostId
    author: UserId
    title: Title
    view_count: Count = 0
    like_count: Count = 0
    created_at: datetime


class PostDetail(PostListItem):
    content: Content
    updated_at: datetime | None = None


class ListPostsQuery(BaseModel):
    q: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=20),
        Field(description="게시글 제목 또는 내용에 포함된 검색어")
    ] = None
    sort: Literal["created_at", "view_count", "like_count"] = "created_at"
    order: Literal["asc", "desc"] = "desc"
    page: Page = 1


class ListPostsResponse(BaseModel):
    data: list[PostListItem]
    pagination: Pagination


class PostCreateRequest(BaseModel):
    title: Title
    content: Content


class PostUpdateRequest(BaseModel):
    title: Title | None = None
    content: Content | None = None

    @model_validator(mode='after')
    def at_least_one_field(self):
        if self.title is None and self.content is None:
            raise ValueError("수정할 필드가 없습니다.")
        return self
