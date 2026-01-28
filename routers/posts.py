import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, func, or_
from db.models.post import Post
from db.models.user import User
from routers.users import CurrentUserId
from schemas.commons import Page, PostId, Pagination, DBSession
from schemas.post import (
    ListPostsQuery,
    PostCreateRequest,
    PostListItem,
    PostUpdateRequest,
    ListPostsResponse,
    PostDetail)

# TODO: liked_count -> Elasticsearch로 성능 개선 고려

PAGE_SIZE = 20

# 정렬 옵션 매핑
def get_order_by(sort: str, order: str) -> list:
    column = getattr(Post, sort)
    ordered = column.desc() if order == "desc" else column.asc()
    if sort != "created_at":
        return [ordered, Post.created_at.desc()]
    return [ordered]


router = APIRouter(
    tags=["POSTS"],
)


async def get_post_or_404(db, post_id: str) -> Post:
    """게시글 조회 (없으면 404)"""
    result = await db.execute(select(Post).where(Post.id == post_id))
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


@router.post("/posts", response_model=PostListItem,
             status_code=status.HTTP_201_CREATED)
async def create_post(author_id: CurrentUserId, post: PostCreateRequest, db: DBSession) -> PostListItem:
    """ 게시글 생성 """
    result = await db.execute(select(User).where(User.id == author_id))
    user = result.scalar_one()

    now = datetime.now(UTC)

    new_post = Post(
        id=f"post_{uuid.uuid4().hex}",
        author_id=author_id,
        title=post.title,
        content=post.content,
        created_at=now,
        updated_at=now,
    )
    new_post.author = user

    db.add(new_post)
    await db.flush()

    return PostDetail.model_validate(new_post)


@router.get("/posts/me", response_model=ListPostsResponse)
async def get_posts_mine(user_id: CurrentUserId, db: DBSession, page: Page = 1) -> ListPostsResponse:
    """내가 작성한 게시글 목록"""
    offset = (page - 1) * PAGE_SIZE

    # 총 개수 조회
    count_result = await db.execute(
        select(func.count()).select_from(Post).where(Post.author_id == user_id)
    )
    total_count = count_result.scalar()
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE or 1

    # 내 게시글 목록 조회
    result = await db.execute(
        select(Post)
        .where(Post.author_id == user_id)
        .order_by(Post.created_at.desc())
        .limit(PAGE_SIZE)
        .offset(offset)
    )
    posts = result.scalars().all()

    return ListPostsResponse(
        data=[PostListItem.model_validate(post) for post in posts],
        pagination=Pagination(page=page, total=total_pages)
    )


@router.get("/posts/{post_id}", response_model=PostDetail)
async def get_single_post(post_id: PostId, db: DBSession) -> PostDetail:
    """게시글 상세 조회"""
    post = await get_post_or_404(db, post_id)
    post.view_count += 1
    await db.flush()

    return PostDetail.model_validate(post)


@router.patch("/posts/{post_id}", response_model=PostDetail)
async def update_post(
        author_id: CurrentUserId, post_id: PostId, update_data: PostUpdateRequest, db: DBSession) -> PostDetail:
    """게시글 수정"""
    post = await get_post_or_404(db, post_id)
    check_post_author(post, author_id)

    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(post, field, value)
    post.updated_at = datetime.now(UTC)

    await db.flush()

    return PostDetail.model_validate(post)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(author_id: CurrentUserId, post_id: PostId, db: DBSession) -> None:
    """게시글 삭제"""
    post = await get_post_or_404(db, post_id)
    check_post_author(post, author_id)
    await db.delete(post)
