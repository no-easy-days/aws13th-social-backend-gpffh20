import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, status, HTTPException

from routers.users import CurrentUserId
from schemas.commons import Page, PostId, Pagination, CurrentCursor
from utils.query import build_set_clause
from schemas.post import (
    ListPostsQuery,
    PostCreateRequest,
    PostListItem,
    PostUpdateRequest,
    ListPostsResponse,
    PostDetail)

# TODO: liked_count -> Elasticsearch로 성능 개선 고려


PAGE_SIZE = 20

# SQL Injection 방어: ORDER BY 절 명시적 매핑
SORT_COLUMN_MAP = {
    "created_at": "created_at",
    "view_count": "view_count",
    "like_count": "like_count",
}
SORT_ORDER_MAP = {
    "asc": "ASC",
    "desc": "DESC",
}

router = APIRouter(
    tags=["POSTS"],
)


async def _get_verified_post(cur, post_id: PostId, author_id: str) -> dict:
    """게시글 존재 여부 + 작성자 검증 후 전체 데이터 반환."""
    await cur.execute(
        "SELECT * FROM posts WHERE id = %s",
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

    # ORDER BY 절 명시적 매핑 (하드코딩된 값만 SQL에 들어감)
    sort_column = SORT_COLUMN_MAP.get(query.sort.value, "created_at")
    sort_order = SORT_ORDER_MAP.get(query.order.value, "DESC")

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
        ORDER BY {sort_column} {sort_order}, created_at DESC
        LIMIT %s OFFSET %s
        """,
        (*search_params, PAGE_SIZE, offset)
    )
    posts = await cur.fetchall()

    return ListPostsResponse(
        data=[PostListItem(**p) for p in posts],
        pagination=Pagination(page=query.page, total=total_pages)
    )


# TODO: id가 아닌 닉네임이 표시되게 하기
@router.post("/posts", response_model=PostListItem,
             status_code=status.HTTP_201_CREATED)
async def create_post(author_id: CurrentUserId, post: PostCreateRequest, cur: CurrentCursor) -> PostListItem:
    """ 게시글 생성 """
    post_id = f"post_{uuid.uuid4().hex}"
    now = datetime.now(UTC)

    await cur.execute(
        """
        INSERT INTO posts (id, author_id, title, content, view_count, like_count, comment_count, created_at, updated_at)
        VALUES (%(id)s, %(author_id)s, %(title)s, %(content)s, %(view_count)s, %(like_count)s, %(comment_count)s, %(created_at)s,
                %(updated_at)s)
        """,
        {
            "id": post_id,
            "author_id": author_id,
            "title": post.title,
            "content": post.content,
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "created_at": now,
            "updated_at": now
        }
    )

    new_post_model = PostDetail(
        id=post_id,
        author_id=author_id,
        title=post.title,
        content=post.content,
        view_count=0,
        like_count=0,
        comment_count=0,
        created_at=now,
        updated_at=now
    )

    return new_post_model


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
        "SELECT * FROM posts WHERE id = %s",
        (post_id,)
    )
    post = await cur.fetchone()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    await cur.execute(
        "UPDATE posts SET view_count = view_count + 1 WHERE id = %s",
        (post_id,)
    )

    return PostDetail(**{**post, "view_count": post["view_count"] + 1})


# SQL Injection 방어: UPDATE 허용 필드 -> DB 컬럼 명시적 매핑
POST_UPDATE_COLUMN_MAP = {
    "title": "title",
    "content": "content",
}


@router.patch("/posts/{post_id}", response_model=PostDetail)
async def update_post(
        author_id: CurrentUserId, post_id: PostId, update_data: PostUpdateRequest, cur: CurrentCursor) -> PostDetail:
    """게시글 수정"""
    post = await _get_verified_post(cur, post_id, author_id)

    # 전달된 필드만 추출 + 안전한 SET 절 생성
    update_fields = update_data.model_dump(exclude_unset=True)
    set_clause, params = build_set_clause(update_fields, POST_UPDATE_COLUMN_MAP)

    if not set_clause:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    now = datetime.now(UTC)
    query_params = {**params, "post_id": post_id, "author_id": author_id, "updated_at": now}

    await cur.execute(
        f"UPDATE posts SET {set_clause}, updated_at = %(updated_at)s WHERE id = %(post_id)s AND author_id = %(author_id)s",
        query_params
    )

    if cur.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # 조회한 데이터 + 변경값으로 응답
    return PostDetail(**{**post, **params, "updated_at": now})


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(author_id: CurrentUserId, post_id: PostId, cur: CurrentCursor) -> None:
    """게시글 삭제"""
    await _get_verified_post(cur, post_id, author_id)
    await cur.execute(
        "DELETE FROM posts WHERE id = %s AND author_id = %s",
        (post_id, author_id)
    )
