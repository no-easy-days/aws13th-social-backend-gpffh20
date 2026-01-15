from datetime import datetime

from pydantic import BaseModel

from schemas.commons import PostId, UserId, Pagination
from schemas.post import Count, Title


class LikedListItem(BaseModel):
    post_id: PostId
    author: UserId
    title: Title
    view_count: Count
    like_count: Count
    created_at: datetime


class ListPostILiked(BaseModel):
    data: list[LikedListItem]
    pagination: Pagination


class LikeStatusResponse(BaseModel):
    liked: bool
    like_count: Count
