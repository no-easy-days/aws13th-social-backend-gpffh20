import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException, status

from config import settings
from routers.users import CurrentUserId
from schemas.commons import PostId, Page, CommentId, Pagination
from schemas.comment import (
    CommentCreateRequest,
    CommentBase,
    CommentUpdateRequest,
    CommentUpdateResponse,
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
def get_comments(post_id: PostId, page: Page = 1) -> CommentListResponse:
    """게시글의 댓글 목록 조회"""
    _verify_post_exists(post_id)
    comments = read_json(settings.comments_file)

    # 해당 게시글의 댓글만 필터링
    post_comments = [c for c in comments if c["post_id"] == post_id]

    # 최신순 정렬
    post_comments.sort(key=lambda c: c["created_at"], reverse=True)

    # 페이지네이션
    paginated_comments, page, total_pages = paginate(post_comments, page, COMMENT_PAGE_SIZE)

    return CommentListResponse(
        data=[CommentBase(**c) for c in paginated_comments],
        pagination=Pagination(page=page, total=total_pages)
    )


@router.post("/posts/{post_id}/comments", response_model=CommentBase,
             status_code=status.HTTP_201_CREATED)
def create_comment(post_id: PostId, user_id: CurrentUserId, comment: CommentCreateRequest) -> CommentBase:
    """댓글 작성"""
    _verify_post_exists(post_id)
    comments = read_json(settings.comments_file)

    comment_id = f"comment_{uuid.uuid4().hex}"
    now = datetime.now(UTC)

    new_comment = {
        "id": comment_id,
        "post_id": post_id,
        "author": user_id,
        "content": comment.content,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    comments.append(new_comment)
    write_json(settings.comments_file, comments)

    return CommentBase(**new_comment)


@router.patch("/posts/{post_id}/comments/{comment_id}", response_model=CommentUpdateResponse)
def update_comment(
        post_id: PostId,
        comment_id: CommentId,
        user_id: CurrentUserId,
        update_data: CommentUpdateRequest
) -> CommentUpdateResponse:
    """댓글 수정"""
    _verify_post_exists(post_id)
    comments = read_json(settings.comments_file)

    comment_index = _get_comment_index_and_verify_author(comments, comment_id, post_id, user_id)

    comments[comment_index]["content"] = update_data.content
    comments[comment_index]["updated_at"] = datetime.now(UTC).isoformat()

    write_json(settings.comments_file, comments)

    return CommentUpdateResponse(**comments[comment_index])


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
