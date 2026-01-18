import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException, status, Response

from config import settings
from routers.users import CurrentUserId
from schemas.commons import PostId, Page, Pagination
from schemas.like import LikedListItem, ListPostILiked, LikeStatusResponse
from utils.data import read_json, write_json
from utils.pagination import paginate

LIKES_PAGE_SIZE = 20

router = APIRouter(
    tags=["LIKES"],
)


def _get_post_or_404(post_id: PostId, posts: list | None = None) -> tuple[dict, list]:
    """게시글 존재 확인 및 반환 (posts 리스트도 함께 반환)"""
    if posts is None:
        posts = read_json(settings.posts_file)
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post, posts


def _update_post_like_count(posts: list, post_id: PostId, delta: int) -> None:
    """게시글의 좋아요 수 업데이트 (posts 리스트를 받아서 처리)"""
    post_index = next((i for i, p in enumerate(posts) if p["id"] == post_id), None)
    if post_index is not None:
        posts[post_index]["like_count"] = posts[post_index].get("like_count", 0) + delta
        write_json(settings.posts_file, posts)


@router.get("/posts/liked", response_model=ListPostILiked)
def get_posts_liked(user_id: CurrentUserId, page: Page = 1):
    """내가 좋아요한 게시글 목록"""
    likes = read_json(settings.likes_file)
    posts = read_json(settings.posts_file)

    # 내가 좋아요한 post_id 목록 (최신순 정렬)
    my_likes = [l for l in likes if l["user_id"] == user_id]
    my_likes.sort(key=lambda l: l["created_at"], reverse=True)
    liked_post_ids = [l["post_id"] for l in my_likes]

    # 좋아요한 게시글 정보 가져오기 (좋아요 순서 유지)
    posts_dict = {p["id"]: p for p in posts}
    liked_posts = [
        posts_dict[post_id] for post_id in liked_post_ids
        if post_id in posts_dict
    ]

    # 페이지네이션
    paginated_posts, actual_page, total_pages = paginate(liked_posts, page, LIKES_PAGE_SIZE)

    return ListPostILiked(
        data=[LikedListItem(
            post_id=p["id"],
            author=p["author"],
            title=p["title"],
            view_count=p.get("view_count", 0),
            like_count=p.get("like_count", 0),
            created_at=p["created_at"]
        ) for p in paginated_posts],
        pagination=Pagination(page=actual_page, total=total_pages)
    )


@router.post("/posts/{post_id}/likes")
def create_like(post_id: PostId, user_id: CurrentUserId):
    """좋아요 등록"""
    _, posts = _get_post_or_404(post_id)
    likes = read_json(settings.likes_file)

    # 이미 좋아요한 경우 확인
    if any(l["post_id"] == post_id and l["user_id"] == user_id for l in likes):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already liked"
        )

    new_like = {
        "id": f"like_{uuid.uuid4().hex}",
        "post_id": post_id,
        "user_id": user_id,
        "created_at": datetime.now(UTC).isoformat(),
    }

    likes.append(new_like)
    write_json(settings.likes_file, likes)

    _update_post_like_count(posts, post_id, 1)

    return {"message": "Liked successfully"}


@router.delete("/posts/{post_id}/likes", status_code=status.HTTP_204_NO_CONTENT)
def delete_like(post_id: PostId, user_id: CurrentUserId):
    """좋아요 취소"""
    _, posts = _get_post_or_404(post_id)
    likes = read_json(settings.likes_file)

    like_index = next(
        (i for i, l in enumerate(likes) if l["post_id"] == post_id and l["user_id"] == user_id),
        None
    )
    if like_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found"
        )

    likes.pop(like_index)
    write_json(settings.likes_file, likes)

    # 게시글 좋아요 수 감소 (이미 읽은 posts 재사용)
    _update_post_like_count(posts, post_id, -1)


@router.get("/posts/{post_id}/likes", response_model=LikeStatusResponse)
def get_like_status(post_id: PostId, user_id: CurrentUserId):
    """좋아요 상태 확인"""
    post, _ = _get_post_or_404(post_id)
    likes = read_json(settings.likes_file)

    is_liked = any(
        l["post_id"] == post_id and l["user_id"] == user_id
        for l in likes
    )

    return LikeStatusResponse(
        liked=is_liked,
        like_count=post.get("like_count", 0)
    )
