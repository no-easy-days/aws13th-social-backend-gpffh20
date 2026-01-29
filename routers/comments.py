import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func

from db.models.comment import Comment
from db.models.post import Post
from routers.users import CurrentUserId
from schemas.commons import PostId, Page, CommentId, Pagination, CurrentCursor, DBSession
from schemas.comment import (
    CommentCreateRequest,
    CommentBase,
    CommentUpdateRequest,
    CommentListResponse,
)

COMMENT_PAGE_SIZE = 10

# TODO: COUNT(*) -> redis 연결로 성능 개선

router = APIRouter(
    tags=["COMMENTS"],
)


async def lock_comment_for_update(db, comment_id: str, post_id: str) -> Comment:
    """댓글 수정/삭제용 (row lock)"""
    result = await db.execute(
        select(Comment).
        where(Comment.id == comment_id, Comment.post_id == post_id)
        .with_for_update()
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    return comment


def check_comment_author(comment: Comment, user_id: str) -> None:
    """작성자 권한 확인 (아니면 403)"""
    if comment.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )


@router.get("/posts/{post_id}/comments", response_model=CommentListResponse)
async def get_comments(post_id: PostId, db: DBSession, page: Page = 1) -> CommentListResponse:
    """게시글의 댓글 목록 조회"""
    # 게시글 존재 확인 + comment_count 조회
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    offset = (page - 1) * COMMENT_PAGE_SIZE
    total_count = post.comment_count
    total_pages = (total_count + COMMENT_PAGE_SIZE - 1) // COMMENT_PAGE_SIZE or 1

    # 댓글 목록 조회 (최신순)
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc())
        .limit(COMMENT_PAGE_SIZE)
        .offset(offset)
    )
    comments = result.scalars().all()

    return CommentListResponse(
        data=[CommentBase.model_validate(c) for c in comments],
        pagination=Pagination(page=page, total=total_pages)
    )


@router.post("/posts/{post_id}/comments", response_model=CommentBase,
             status_code=status.HTTP_201_CREATED)
async def create_comment(
        post_id: PostId, user_id: CurrentUserId, comment: CommentCreateRequest, db: DBSession) -> CommentBase:
    """댓글 작성"""
    new_comment = Comment(
        id=f"comment_{uuid.uuid4().hex}",
        post_id=post_id,
        author_id=user_id,
        content=comment.content,
    )

    db.add(new_comment)
    await db.flush()
    await db.refresh(new_comment)

    return CommentBase.model_validate(new_comment)


@router.patch("/posts/{post_id}/comments/{comment_id}", response_model=CommentBase)
async def update_comment(
        post_id: PostId,
        comment_id: CommentId,
        user_id: CurrentUserId,
        update_data: CommentUpdateRequest,
        db: DBSession,
) -> CommentBase:
    """댓글 수정"""
    comment = await lock_comment_for_update(db, comment_id, post_id)
    check_comment_author(comment, user_id)

    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(comment, field, value)

    await db.flush()
    await db.refresh(comment)

    return CommentBase.model_validate(comment)




@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
        post_id: PostId, comment_id: CommentId, user_id: CurrentUserId, db: DBSession) -> None:
    """댓글 삭제"""
    comment = await lock_comment_for_update(db, comment_id, post_id)
    check_comment_author(comment, user_id)

    await db.delete(comment)


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
