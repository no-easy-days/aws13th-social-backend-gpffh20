from typing import Annotated

from pydantic import Field, BaseModel

UserId = Annotated[
    str,
    Field(
        pattern=r"^user_\d+$",
        description="사용자 ID",
        examples=["user_123"],
    ),
]

PostId = Annotated[
    str,
    Field(
        pattern=r"^post_\d+$",
        description="게시글 ID",
        examples=["post_123"],
    ),
]

Page = Annotated[
    int,
    Field(default=1, ge=1, le=10000, description="조회할 페이지 번호"),
]


class Pagination(BaseModel):
    page: Page
    total: Annotated[int, Field(ge=0)]