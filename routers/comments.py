import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException, status
from pymysql import IntegrityError

from routers.users import CurrentUserId
from schemas.commons import PostId, Page, CommentId, Pagination, CurrentCursor
from utils.query import build_set_clause
from schemas.comment import (
    CommentCreateRequest,
    CommentBase,
    CommentUpdateRequest,
    CommentListResponse,
)

COMMENT_PAGE_SIZE = 10

# TODO: COUNT(*) -> redis 연결로 성능 개선

# SQL Injection 방어: UPDATE 허용 필드 -> DB 컬럼 명시적 매핑
COMMENT_UPDATE_COLUMN_MAP = {
    "content": "content",
}

router = APIRouter(
    tags=["COMMENTS"],
)


@router.get("/posts/{post_id}/comments", response_model=CommentListResponse)
async def get_comments(post_id: PostId, cur: CurrentCursor, page: Page = 1) -> CommentListResponse:
    """게시글의 댓글 목록 조회"""
    # 게시글 존재 확인
    await cur.execute(
        "SELECT id FROM posts WHERE id = %s",
        (post_id,)
    )
    if not await cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    offset = (page - 1) * COMMENT_PAGE_SIZE

    # 총 개수 조회
    await cur.execute(
        "SELECT comment_count as total FROM posts WHERE post_id = %s",
        (post_id,)
    )
    total_count = (await cur.fetchone())["total"]
    total_pages = (total_count + COMMENT_PAGE_SIZE - 1) // COMMENT_PAGE_SIZE or 1

    # 댓글 목록 조회 (최신순)
    await cur.execute(
        """
        SELECT id, post_id, author_id, content, created_at
        FROM comments
        WHERE post_id = %(post_id)s
        ORDER BY created_at DESC
        LIMIT %(page_size)s OFFSET %(offset)s
        """,
        {
            "post_id": post_id,
            "page_size": COMMENT_PAGE_SIZE,
            "offset": offset
        }
    )
    comments = await cur.fetchall()

    return CommentListResponse(
        data=[CommentBase(**c) for c in comments],
        pagination=Pagination(page=page, total=total_pages)
    )


@router.post("/posts/{post_id}/comments", response_model=CommentBase,
             status_code=status.HTTP_201_CREATED)
async def create_comment(
        post_id: PostId, user_id: CurrentUserId, comment: CommentCreateRequest, cur: CurrentCursor) -> CommentBase:
    """댓글 작성"""
    comment_id = f"comment_{uuid.uuid4().hex}"
    now = datetime.now(UTC)

    try:
        await cur.execute(
            """
            INSERT INTO comments (id, post_id, author_id, content, created_at)
            VALUES (%(comment_id)s, %(post_id)s, %(author_id)s, %(content)s, %(created_at)s)
            """,
            {
                "comment_id": comment_id,
                "post_id": post_id,
                "author_id": user_id,
                "content": comment.content,
                "created_at": now
            }
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return CommentBase(
        id=comment_id,
        post_id=post_id,
        author_id=user_id,
        content=comment.content,
        created_at=now,
    )


@router.patch("/posts/{post_id}/comments/{comment_id}", response_model=CommentBase)
async def update_comment(
        post_id: PostId,
        comment_id: CommentId,
        user_id: CurrentUserId,
        update_data: CommentUpdateRequest,
        cur: CurrentCursor
) -> CommentBase:
    """댓글 수정"""
    # 댓글 조회 + 작성자 확인
    await cur.execute(
        "SELECT id, post_id, author_id, content, created_at FROM comments WHERE id = %s AND post_id = %s",
        (comment_id, post_id)
    )
    comment = await cur.fetchone()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment["author_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this comment"
        )

    # 안전한 SET 절 생성
    update_fields = update_data.model_dump(exclude_unset=True)
    set_clause, params = build_set_clause(update_fields, COMMENT_UPDATE_COLUMN_MAP)

    if not set_clause:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    query_params = {**params, "comment_id": comment_id, "author_id": user_id}

    await cur.execute(
        f"UPDATE comments SET {set_clause} WHERE id = %(comment_id)s AND author_id = %(author_id)s",
        query_params
    )
    if cur.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    return CommentBase(
        id=comment["id"],
        post_id=comment["post_id"],
        author_id=comment["author_id"],
        content=params.get("content", comment["content"]),
        created_at=comment["created_at"],
    )

@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
        post_id: PostId, comment_id: CommentId, user_id: CurrentUserId, cur: CurrentCursor) -> None:
    """댓글 삭제"""
    # 댓글 존재 + 작성자 확인
    await cur.execute(
        "SELECT author_id FROM comments WHERE id = %s AND post_id = %s",
        (comment_id, post_id)
    )
    comment = await cur.fetchone()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    if comment["author_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )

    await cur.execute(
        "DELETE FROM comments WHERE id = %s AND author_id = %s",
        (comment_id, user_id)
    )


@router.get("/comments/me", response_model=CommentListResponse)
async def get_comments_mine(user_id: CurrentUserId, cur: CurrentCursor, page: Page = 1) -> CommentListResponse:
    """내가 작성한 댓글 목록"""
    offset = (page - 1) * COMMENT_PAGE_SIZE

    # 총 개수 조회
    await cur.execute(
        "SELECT COUNT(*) as total FROM comments WHERE author_id = %s",
        (user_id,)
    )
    total_count = (await cur.fetchone())["total"]
    total_pages = (total_count + COMMENT_PAGE_SIZE - 1) // COMMENT_PAGE_SIZE or 1

    # 내 댓글 목록 조회 (최신순)
    await cur.execute(
        """
        SELECT id, post_id, author_id, content, created_at
        FROM comments
        WHERE author_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (user_id, COMMENT_PAGE_SIZE, offset)
    )
    comments = await cur.fetchall()

    return CommentListResponse(
        data=[CommentBase(**c) for c in comments],
        pagination=Pagination(page=page, total=total_pages)
    )
