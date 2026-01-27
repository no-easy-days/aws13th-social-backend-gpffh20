from datetime import datetime, UTC

from aiomysql import IntegrityError
from fastapi import APIRouter, HTTPException, status

from routers.users import CurrentUserId
from schemas.commons import PostId, Page, Pagination, CurrentCursor
from schemas.like import LikedListItem, ListPostILiked, LikeStatusResponse

LIKES_PAGE_SIZE = 20

router = APIRouter(
    tags=["LIKES"],
)


@router.get("/posts/liked", response_model=ListPostILiked)
async def get_posts_liked(user_id: CurrentUserId, cur: CurrentCursor, page: Page = 1) -> ListPostILiked:
    """내가 좋아요한 게시글 목록"""
    offset = (page - 1) * LIKES_PAGE_SIZE

    # 총 개수 조회
    await cur.execute(
        "SELECT COUNT(*) as total FROM likes WHERE user_id = %s",
        (user_id,)
    )
    total_count = (await cur.fetchone())["total"]
    total_pages = (total_count + LIKES_PAGE_SIZE - 1) // LIKES_PAGE_SIZE or 1

    await cur.execute(
        """
        SELECT p.id as post_id, p.author_id as author, p.title, p.view_count, p.like_count, p.created_at
        FROM likes l
        JOIN posts p ON l.post_id = p.id
        WHERE l.user_id = %s
        ORDER BY l.created_at DESC
        LIMIT %s OFFSET %s
        """,
        (user_id, LIKES_PAGE_SIZE, offset)
    )
    liked_posts = await cur.fetchall()

    return ListPostILiked(
        data=[LikedListItem(**post) for post in liked_posts],
        pagination=Pagination(page=page, total=total_pages)
    )


@router.post("/posts/{post_id}/likes", response_model=LikeStatusResponse,
             status_code=status.HTTP_201_CREATED)
async def create_like(post_id: PostId, user_id: CurrentUserId, cur: CurrentCursor) -> LikeStatusResponse:
    """좋아요 등록"""
    # 게시글 존재 확인
    await cur.execute("SELECT id FROM posts WHERE id = %s", (post_id,))
    if not await cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # 좋아요 등록 (복합 PK이므로 중복 시 IntegrityError)
    now = datetime.now(UTC)
    try:
        await cur.execute(
            "INSERT INTO likes (post_id, user_id, created_at) VALUES (%(post_id)s, %(user_id)s, %(created_at)s)",
            {
                "post_id": post_id,
                "user_id": user_id,
                "created_at":now
            }
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already liked"
        )

    # 트리거가 like_count 자동 증가
    await cur.execute("SELECT like_count FROM posts WHERE id = %s", (post_id,))
    post = await cur.fetchone()

    return LikeStatusResponse(
        liked=True,
        like_count=post["like_count"] if post else 1,
    )


@router.delete("/posts/{post_id}/likes", response_model=LikeStatusResponse)
async def delete_like(post_id: PostId, user_id: CurrentUserId, cur: CurrentCursor) -> LikeStatusResponse:
    """좋아요 취소"""
    await cur.execute(
        "DELETE FROM likes WHERE post_id = %s AND user_id = %s",
        (post_id, user_id)
    )

    if cur.rowcount == 0:
        await cur.execute("SELECT id FROM posts WHERE id = %s", (post_id,))
        if not await cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Like not found"
        )

    # 트리거가 like_count 자동 감소
    await cur.execute("SELECT like_count FROM posts WHERE id = %s", (post_id,))
    post = await cur.fetchone()

    return LikeStatusResponse(
        liked=False,
        like_count=post["like_count"] if post else 0,
    )



@router.get("/posts/{post_id}/likes", response_model=LikeStatusResponse)
async def get_like_status(post_id: PostId, user_id: CurrentUserId, cur: CurrentCursor) -> LikeStatusResponse:
    """좋아요 상태 확인"""
    await cur.execute("SELECT like_count FROM posts WHERE id = %s", (post_id,))
    post = await cur.fetchone()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # 좋아요 여부 확인
    await cur.execute(
        "SELECT 1 FROM likes WHERE post_id = %s AND user_id = %s",
        (post_id, user_id)
    )
    is_liked = await cur.fetchone() is not None

    return LikeStatusResponse(
        liked=is_liked,
        like_count=post["like_count"]
    )
