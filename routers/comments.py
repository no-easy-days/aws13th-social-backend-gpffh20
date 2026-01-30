import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from db.models.comment import Comment
from db.models.post import Post
from routers.users import CurrentUserId
from schemas.commons import PostId, Page, CommentId, Pagination, DBSession
from schemas.comment import (
    CommentCreateRequest,
    CommentItemBase,
    CommentListItem,
    CommentUpdateRequest,
    CommentListResponse,
    MyCommentListResponse,
)

COMMENT_PAGE_SIZE = 10


router = APIRouter(
    tags=["COMMENTS"],
)


async def lock_comment_for_update(db, comment_id: str, post_id: str, load_author: bool = False) -> Comment:
    """댓글 수정/삭제용 (row lock)"""
    query = select(Comment).where(Comment.id == comment_id, Comment.post_id == post_id)
    if load_author:
        query = query.options(joinedload(Comment.author))
    query = query.with_for_update()

    result = await db.execute(query)
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
        .options(joinedload(Comment.author))
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc())
        .limit(COMMENT_PAGE_SIZE)
        .offset(offset)
    )
    comments = result.unique().scalars().all()

    return CommentListResponse(
        data=[CommentListItem.model_validate(c) for c in comments],
        pagination=Pagination(page=page, total=total_pages)
    )


async def get_comment_with_author(db, comment_id: str) -> Comment:
    """댓글 + author 조회"""
    result = await db.execute(
        select(Comment)
        .options(joinedload(Comment.author))
        .where(Comment.id == comment_id)
    )
    return result.scalar_one()


@router.post("/posts/{post_id}/comments", response_model=CommentListItem,
             status_code=status.HTTP_201_CREATED)
async def create_comment(
        post_id: PostId, user_id: CurrentUserId, comment: CommentCreateRequest, db: DBSession) -> CommentListItem:
    """댓글 작성"""
    new_comment = Comment(
        id=f"comment_{uuid.uuid4().hex}",
        post_id=post_id,
        author_id=user_id,
        content=comment.content,
    )

    db.add(new_comment)
    await db.flush()

    comment_with_author = await get_comment_with_author(db, new_comment.id)
    return CommentListItem.model_validate(comment_with_author)


@router.patch("/posts/{post_id}/comments/{comment_id}", response_model=CommentListItem)
async def update_comment(
        post_id: PostId,
        comment_id: CommentId,
        user_id: CurrentUserId,
        update_data: CommentUpdateRequest,
        db: DBSession,
) -> CommentListItem:
    """댓글 수정"""
    comment = await lock_comment_for_update(db, comment_id, post_id, load_author=True)
    check_comment_author(comment, user_id)

    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(comment, field, value)

    await db.flush()

    return CommentListItem.model_validate(comment)




@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
        post_id: PostId, comment_id: CommentId, user_id: CurrentUserId, db: DBSession) -> None:
    """댓글 삭제"""
    comment = await lock_comment_for_update(db, comment_id, post_id)
    check_comment_author(comment, user_id)

    await db.delete(comment)


@router.get("/comments/me", response_model=MyCommentListResponse)
async def get_comments_mine(user_id: CurrentUserId, db: DBSession, page: Page = 1) -> MyCommentListResponse:
    """내가 작성한 댓글 목록"""
    offset = (page - 1) * COMMENT_PAGE_SIZE

    # 총 개수 조회
    total_count = (await db.execute(
        select(func.count()).select_from(Comment).where(Comment.author_id == user_id)
    )).scalar()
    total_pages = (total_count + COMMENT_PAGE_SIZE - 1) // COMMENT_PAGE_SIZE or 1

    # 내 댓글 목록 조회 (최신순)
    result = await db.execute(
        select(Comment)
        .where(Comment.author_id == user_id)
        .order_by(Comment.created_at.desc())
        .limit(COMMENT_PAGE_SIZE)
        .offset(offset)
    )
    comments = result.scalars().all()

    return MyCommentListResponse(
        data=[CommentItemBase.model_validate(c) for c in comments],
        pagination=Pagination(page=page, total=total_pages)
    )
