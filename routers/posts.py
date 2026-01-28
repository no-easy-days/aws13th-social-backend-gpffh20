import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from db.models.post import Post
from db.models.user import User
from routers.users import CurrentUserId
from schemas.commons import Page, PostId, Pagination, CurrentCursor, DBSession
from schemas.post import (
    ListPostsQuery,
    PostCreateRequest,
    PostListItem,
    PostUpdateRequest,
    ListPostsResponse,
    PostDetail)

# TODO: liked_count -> Elasticsearch로 성능 개선 고려

PAGE_SIZE = 20

# SQL Injection 방어: ORDER BY 절 전체 하드코딩
ORDER_BY_MAP = {
    ("created_at", "desc"): "ORDER BY created_at DESC",
    ("created_at", "asc"): "ORDER BY created_at ASC",
    ("view_count", "desc"): "ORDER BY view_count DESC, created_at DESC",
    ("view_count", "asc"): "ORDER BY view_count ASC, created_at DESC",
    ("like_count", "desc"): "ORDER BY like_count DESC, created_at DESC",
    ("like_count", "asc"): "ORDER BY like_count ASC, created_at DESC",
}

# UPDATE 허용 필드 whitelist
ALLOWED_POST_UPDATE_FIELDS = frozenset(["title", "content"])

POST_SET_CLAUSE_MAP = {
    frozenset(["title"]): "title = %(title)s",
    frozenset(["content"]): "content = %(content)s",
    frozenset(["title", "content"]): "title = %(title)s, content = %(content)s",
}

router = APIRouter(
    tags=["POSTS"],
)


async def _get_verified_post(cur, post_id: PostId, author_id: str) -> dict:
    """게시글 존재 여부 + 작성자 검증 후 전체 데이터 반환."""
    await cur.execute(
        "SELECT * FROM posts WHERE id = %s FOR UPDATE",
        (post_id,)
    )
    post = await cur.fetchone()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post["author_id"] != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this post"
        )

    return post


@router.get("/posts", response_model=ListPostsResponse)
async def get_posts(cur: CurrentCursor, query: ListPostsQuery = Depends()) -> ListPostsResponse:
    """
    게시글 전체 목록 조회
    - 검색
    - 정렬(조회수, 좋아요수, 최신순)
    - 페이지네이션 (20개씩)
    """
    offset = (query.page - 1) * PAGE_SIZE

    # ORDER BY 절 전체 하드코딩 + 검증
    order_by_key = (query.sort.value, query.order.value)
    assert order_by_key in ORDER_BY_MAP, f"Invalid sort: {order_by_key}"
    order_by_clause = ORDER_BY_MAP[order_by_key]

    # 검색 조건
    if query.q:
        search_pattern = f"%{query.q}%"
        where_clause = "WHERE title LIKE %s OR content LIKE %s"
        search_params = (search_pattern, search_pattern)
    else:
        where_clause = ""
        search_params = ()

    # 총 개수 조회
    await cur.execute(
        f"SELECT COUNT(*) as total FROM posts {where_clause}",
        search_params
    )
    total_count = (await cur.fetchone())["total"]
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE or 1

    # 게시글 목록 조회
    await cur.execute(
        f"""
        SELECT id, author_id, title, view_count, like_count, comment_count, created_at
        FROM posts
        {where_clause}
        {order_by_clause}
        LIMIT %s OFFSET %s
        """,
        (*search_params, PAGE_SIZE, offset)
    )
    posts = await cur.fetchall()

    return ListPostsResponse(
        data=[PostListItem(**p) for p in posts],
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
async def get_posts_mine(user_id: CurrentUserId, cur: CurrentCursor, page: Page = 1) -> ListPostsResponse:
    """내가 작성한 게시글 목록"""
    offset = (page - 1) * PAGE_SIZE

    # 총 개수 조회
    await cur.execute(
        "SELECT COUNT(*) as total FROM posts WHERE author_id = %s",
        (user_id,)
    )
    total_count = (await cur.fetchone())["total"]
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE or 1

    # 내 게시글 목록 조회
    # TODO: 트래픽 많아지면 redis 처리 고려
    await cur.execute(
        """
        SELECT id, author_id, title, view_count, like_count, comment_count, created_at
        FROM posts
        WHERE author_id = %(author_id)s
        ORDER BY created_at DESC
        LIMIT %(page_size)s OFFSET %(offset)s
        """,
        {
            "author_id": user_id,
            "page_size": PAGE_SIZE,
            "offset": offset
        }
    )
    posts = await cur.fetchall()

    return ListPostsResponse(
        data=[PostListItem(**post) for post in posts],
        pagination=Pagination(page=page, total=total_pages)
    )


@router.get("/posts/{post_id}", response_model=PostDetail)
async def get_single_post(post_id: PostId, cur: CurrentCursor) -> PostDetail:
    """게시글 상세 조회"""
    await cur.execute(
        "UPDATE posts SET view_count = view_count + 1 WHERE id = %s",
        (post_id,)
    )

    await cur.execute(
        "SELECT * FROM posts WHERE id = %s",
        (post_id,)
    )

    updated_post = await cur.fetchone()
    if updated_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    return PostDetail(**updated_post)


@router.patch("/posts/{post_id}", response_model=PostDetail)
async def update_post(
        author_id: CurrentUserId, post_id: PostId, update_data: PostUpdateRequest, cur: CurrentCursor) -> PostDetail:
    """게시글 수정"""
    post = await _get_verified_post(cur, post_id, author_id)

    # whitelist 검증 + SET 절 하드코딩 매핑
    update_fields = update_data.model_dump(exclude_unset=True)
    field_keys = frozenset(update_fields.keys())
    if not field_keys.issubset(ALLOWED_POST_UPDATE_FIELDS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid fields: {field_keys}"
        )

    set_clause = POST_SET_CLAUSE_MAP.get(field_keys)
    if not set_clause:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    now = datetime.now(UTC)
    query_params = {**update_fields, "post_id": post_id, "author_id": author_id, "updated_at": now}

    await cur.execute(
        "UPDATE posts SET " + set_clause + ", updated_at = %(updated_at)s WHERE id = %(post_id)s AND author_id = %(author_id)s",
        query_params
    )

    if cur.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # 조회한 데이터 + 변경값으로 응답
    return PostDetail(**{**post, **update_fields, "updated_at": now})


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(author_id: CurrentUserId, post_id: PostId, db: DBSession) -> None:
    """게시글 삭제"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    if post.author_id != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    await db.delete(post)