from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import StringConstraints, BaseModel, Field, model_validator, ConfigDict, computed_field

from schemas.commons import PostId, UserId, Pagination, Page, Content, Title, Count


class SortColumn(str, Enum):
    CREATED_AT = "created_at"
    VIEW_COUNT = "view_count"
    LIKE_COUNT = "like_count"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class PostListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PostId
    author_id: UserId
    author: Any = Field(exclude=True)
    title: Title
    view_count: Count = 0
    like_count: Count = 0
    comment_count: Count = 0
    created_at: datetime

    @computed_field
    @property
    def author_nickname(self) -> str:
        return self.author.nickname if self.author else "Unknown"


class PostDetail(PostListItem):
    content: Content
    updated_at: datetime | None = None


class ListPostsQuery(BaseModel):
    model_config = ConfigDict(extra='forbid')

    q: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=20),
        Field(description="게시글 제목 또는 내용에 포함된 검색어")
    ] = None
    sort: SortColumn = SortColumn.CREATED_AT
    order: SortOrder = SortOrder.DESC
    page: Page = 1


class ListPostsResponse(BaseModel):
    data: list[PostListItem]
    pagination: Pagination


class PostCreateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    title: Title
    content: Content


class PostUpdateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    title: Title | None = None
    content: Content | None = None

    @model_validator(mode='after')
    def at_least_one_field(self):
        if self.title is None and self.content is None:
            raise ValueError("수정할 필드가 없습니다.")
        return self
