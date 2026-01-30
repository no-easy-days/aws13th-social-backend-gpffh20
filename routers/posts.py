import asyncio
import uuid
import logging
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, func, or_, update
from db.models.post import Post
from db.session import AsyncSessionLocal
from schemas.commons import Page, PostId, Pagination, DBSession, CurrentUserId
from schemas.post import (
    ListPostsQuery,
    PostCreateRequest,
    PostCreateResponse,
    PostListItem,
    PostUpdateRequest,
    ListPostsResponse,
    MyPostListItem,
    MyPostsResponse,
    PostDetail)
from utils.redis import get_redis

# TODO: liked_count -> Elasticsearch로 성능 개선 고려

PAGE_SIZE = 20
SORT_COLUMN_MAP = {
    'created_at': Post.created_at,
    'view_count': Post.view_count,
    'like_count': Post.like_count
}
logger = logging.getLogger(__name__)


def get_order_by(sort: str, order: str) -> list:
    """정렬 옵션 매핑"""
    column = SORT_COLUMN_MAP.get(sort)
    if column is None:
        raise ValueError(f"Invalid sort field: {sort}")

    ordered = column.desc() if order == "desc" else column.asc()
    if sort != "created_at":
        return [ordered, Post.created_at.desc()]
    return [ordered]


router = APIRouter(
    tags=["POSTS"],
)


async def lock_post_for_update(db, post_id: str) -> Post:
    """게시글 수정/삭제용 (row lock)"""
    result = await db.execute(
        select(Post).where(Post.id == post_id).with_for_update()
    )
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post


def check_post_author(post: Post, author_id: str) -> None:
    """작성자 권한 확인 (아니면 403)"""
    if post.author_id != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )


@router.get("/posts", response_model=ListPostsResponse)
async def get_posts(db: DBSession, query: ListPostsQuery = Depends()) -> ListPostsResponse:
    """
    게시글 전체 목록 조회
    - 검색
    - 정렬(조회수, 좋아요수, 최신순)
    - 페이지네이션 (20개씩)
    """
    offset = (query.page - 1) * PAGE_SIZE

    # 검색 조건
    where_condition = None
    if query.q:
        search_pattern = f"%{query.q}%"
        where_condition = or_(
            Post.title.like(search_pattern),
            Post.content.like(search_pattern)
        )

    # 총 개수 조회
    count_query = select(func.count()).select_from(Post)
    if where_condition is not None:
        count_query = count_query.where(where_condition)
    count_result = await db.execute(count_query)
    total_count = count_result.scalar()
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE or 1

    # 게시글 목록 조회
    posts_query = select(Post)
    if where_condition is not None:
        posts_query = posts_query.where(where_condition)
    posts_query = posts_query.order_by(*get_order_by(query.sort.value, query.order.value))
    posts_query = posts_query.limit(PAGE_SIZE).offset(offset)

    result = await db.execute(posts_query)
    posts = result.scalars().all()

    return ListPostsResponse(
        data=[PostListItem.model_validate(post) for post in posts],
        pagination=Pagination(page=query.page, total=total_pages)
    )


@router.post("/posts", response_model=PostCreateResponse,
             status_code=status.HTTP_201_CREATED)
async def create_post(author_id: CurrentUserId, post: PostCreateRequest, db: DBSession) -> PostCreateResponse:
    """ 게시글 생성 """
    new_post = Post(
        id=f"post_{uuid.uuid4().hex}",
        author_id=author_id,
        title=post.title,
        content=post.content,
    )

    db.add(new_post)
    await db.flush()
    await db.refresh(new_post)

    return PostCreateResponse.model_validate(new_post)


@router.get("/posts/me", response_model=MyPostsResponse)
async def get_posts_mine(user_id: CurrentUserId, db: DBSession, page: Page = 1) -> MyPostsResponse:
    """내가 작성한 게시글 목록"""
    offset = (page - 1) * PAGE_SIZE

    # 총 개수 조회
    total_count = await db.execute(
        select(func.count()).select_from(Post).where(Post.author_id == user_id)
    )
    total_pages = (total_count.scalar() + PAGE_SIZE - 1) // PAGE_SIZE or 1

    # 내 게시글 목록 조회
    result = await db.execute(
        select(Post)
        .where(Post.author_id == user_id)
        .order_by(Post.created_at.desc())
        .limit(PAGE_SIZE)
        .offset(offset)
    )
    posts = result.scalars().all()

    return MyPostsResponse(
        data=[MyPostListItem.model_validate(post) for post in posts],
        pagination=Pagination(page=page, total=total_pages)
    )


async def flush_view_counts():
    redis = get_redis()
    cursor = 0
    keys = []

    while True:
        cursor, partial_keys = await redis.scan(cursor, match="views:*", count=100)
        keys.extend(partial_keys)
        if cursor == 0:
            break

    if not keys:
        return

    async with AsyncSessionLocal() as db:
        for key in keys:
            post_id = key.split(":")[1]
            count = await redis.getdel(key)

            if count:
                await db.execute(
                    update(Post)
                    .where(Post.id == post_id)
                    .values(view_count=Post.view_count + int(count))
                )
        await db.commit()


async def view_count_scheduler(interval_seconds: int = 300):
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await flush_view_counts()
            logger.info(f"[Scheduler] View count flushed")
        except Exception as e:
            logger.error(f"[Scheduler] View count failed: {e}", exc_info=True)


@router.get("/posts/{post_id}", response_model=PostDetail)
async def get_single_post(post_id: PostId, db: DBSession) -> PostDetail:
    """게시글 상세 조회"""
    result = await db.execute(
        select(Post).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    redis = get_redis()
    cached_views = await redis.incr(f"views:{post_id}")

    response = PostDetail.model_validate(post)
    response.view_count = post.view_count + cached_views
    return response


@router.patch("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_post(
        author_id: CurrentUserId, post_id: PostId, update_data: PostUpdateRequest, db: DBSession) -> None:
    """게시글 수정"""
    post = await lock_post_for_update(db, post_id)
    check_post_author(post, author_id)

    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(post, field, value)
    post.updated_at = datetime.now(UTC)

    await db.flush()


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(author_id: CurrentUserId, post_id: PostId, db: DBSession) -> None:
    """게시글 삭제"""
    post = await lock_post_for_update(db, post_id)
    check_post_author(post, author_id)
    await db.delete(post)
