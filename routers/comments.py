import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException, status

from config import settings
from routers.users import CurrentUserId
from schemas.commons import PostId, Page, CommentId, Pagination, CurrentCursor
from schemas.comment import (
    CommentCreateRequest,
    CommentBase,
    CommentUpdateRequest,
    # CommentUpdateResponse,
    CommentListResponse,
)
from utils.database import read_json, write_json
from utils.pagination import paginate

COMMENT_PAGE_SIZE = 10

router = APIRouter(
    tags=["COMMENTS"],
)

def _get_comment_index_and_verify_author(
    comments: list, comment_id: CommentId, post_id: PostId, author_id: str
) -> int:
    comment_index = next(
        (i for i, c in enumerate(comments) if c["id"] == comment_id and c["post_id"] == post_id),
        None
    )
    if comment_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    if comments[comment_index]["author"] != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this comment"
        )
    return comment_index


def _verify_post_exists(post_id: PostId) -> None:
    """게시글 존재 확인"""
    posts = read_json(settings.posts_file)

    if not any(p["id"] == post_id for p in posts):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
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
        "SELECT COUNT(*) as total FROM comments WHERE post_id = %s",
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

    comment_id = f"comment_{uuid.uuid4().hex}"
    now = datetime.now(UTC)

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

    return CommentBase(
        id=comment_id,
        post_id=post_id,
        author_id=user_id,
        content=comment.content,
        created_at=now,
    )


@router.patch("/posts/{post_id}/comments/{comment_id}", response_model=CommentBase)
def update_comment(
        post_id: PostId,
        comment_id: CommentId,
        user_id: CurrentUserId,
        update_data: CommentUpdateRequest
) -> CommentBase:
    """댓글 수정"""
    _verify_post_exists(post_id)
    comments = read_json(settings.comments_file)

    comment_index = _get_comment_index_and_verify_author(comments, comment_id, post_id, user_id)

    comments[comment_index]["content"] = update_data.content
    comments[comment_index]["updated_at"] = datetime.now(UTC).isoformat()

    write_json(settings.comments_file, comments)

    return CommentBase(**comments[comment_index])


@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(post_id: PostId, comment_id: CommentId, user_id: CurrentUserId) -> None:
    """댓글 삭제"""
    _verify_post_exists(post_id)
    comments = read_json(settings.comments_file)

    comment_index = _get_comment_index_and_verify_author(comments, comment_id, post_id, user_id)

    comments.pop(comment_index)
    write_json(settings.comments_file, comments)


@router.get("/comments/me", response_model=CommentListResponse)
def get_comments_mine(user_id: CurrentUserId, page: Page = 1) -> CommentListResponse:
    """내가 작성한 댓글 목록"""
    comments = read_json(settings.comments_file)

    my_comments = [c for c in comments if c["author"] == user_id]

    # 최신순 정렬
    my_comments.sort(key=lambda c: c["created_at"], reverse=True)

    # 페이지네이션
    paginated_comments, page, total_pages = paginate(my_comments, page, COMMENT_PAGE_SIZE)

    return CommentListResponse(
        data=[CommentBase(**c) for c in paginated_comments],
        pagination=Pagination(page=page, total=total_pages)
    )
