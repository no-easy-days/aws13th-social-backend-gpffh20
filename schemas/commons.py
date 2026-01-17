from typing import Annotated

from pydantic import Field, BaseModel, StringConstraints

UserId = Annotated[
    str,
    Field(
        pattern=r"^user_[a-f0-9]+$",
        description="사용자 ID",
        examples=["user_a1b2c3d4"],
    ),
]

PostId = Annotated[
    str,
    Field(
        pattern=r"^post_[a-f0-9]+$",
        description="게시글 ID",
        examples=["post_a1b2c3d4"],
    ),
]

CommentId = Annotated[
    str,
    Field(
        pattern=r"^comment_\d+$",
        description="댓글 ID",
        examples=["comment_123"],
    )
]

Page = Annotated[
    int,
    Field(default=1, ge=1, le=10000, description="조회할 페이지 번호"),
]

Content = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]
Title = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
]

Count = Annotated[int, Field(ge=0)]


class Pagination(BaseModel):
    page: Page
    total: Annotated[int, Field(ge=0, description="전체 페이지 수")]
