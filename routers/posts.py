import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, status, HTTPException

from config import settings
from routers.users import CurrentUserId
from schemas.commons import Page, PostId, Pagination
from schemas.post import (
    ListPostsQuery,
    PostCreateRequest,
    PostListItem,
    PostUpdateRequest,
    ListPostsResponse,
    PostDetail)
from utils.database import read_json, write_json
from utils.pagination import paginate

PAGE_SIZE = 20

router = APIRouter(
    tags=["POSTS"],
)


def _get_post_index_and_verify_author(posts: list, post_id: PostId, author_id: str) -> int:
    post_index = next((i for i, post in enumerate(posts) if post["id"] == post_id), None)
    if post_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="post not found"
        )
    post = posts[post_index]
    if post["author"] != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not authorized to modify this post"
        )
    return post_index


@router.get("/posts", response_model=ListPostsResponse)
def get_posts(query: ListPostsQuery = Depends()) -> ListPostsResponse:
    """
    게시글 전체 목록 조회
    - 검색
    - 정렬(조회수, 좋아요수, 최신순)
    - 페이지네이션 (20개씩)
    """
    posts = read_json(settings.posts_file)

    # 검색
    if query.q:
        q_lower = query.q.lower()
        posts = [
            post for post in posts
            if q_lower in post["title"].lower() or q_lower in post["content"].lower()
        ]
    # 정렬
    reverse = query.order == "desc"
    posts.sort(key=lambda p: p.get(query.sort, 0), reverse=reverse)

    # 페이지네이션
    paginated_posts, page, total_pages = paginate(posts, query.page, PAGE_SIZE)

    return ListPostsResponse(
        data=[PostListItem(**p) for p in paginated_posts],
        pagination=Pagination(page=page, total=total_pages)
    )


# TODO: id가 아닌 닉네임이 표시되게 하기
@router.post("/posts", response_model=PostListItem,
             status_code=status.HTTP_201_CREATED)
def create_post(author_id: CurrentUserId, post: PostCreateRequest) -> PostListItem:
    """ 게시글 생성 """
    posts = read_json(settings.posts_file)

    post_id = f"post_{uuid.uuid4().hex}"
    now = datetime.now(UTC)

    new_post_model = PostDetail(
        id=post_id,
        author=author_id,
        title=post.title,
        content=post.content,
        view_count=0,
        like_count=0,
        created_at=now,
        updated_at=now,
    )

    posts.append(new_post_model.model_dump(mode="json"))
    write_json(settings.posts_file, posts)
    return new_post_model


@router.get("/posts/me", response_model=ListPostsResponse)
def get_posts_mine(user_id: CurrentUserId, page: Page = 1) -> ListPostsResponse:
    """내가 작성한 게시글 목록"""
    posts = read_json(settings.posts_file)

    my_posts = [post for post in posts if post["author"] == user_id]

    my_posts.sort(key=lambda post: post["created_at"], reverse=True)

    paginated_posts, page, total_pages = paginate(my_posts, page, PAGE_SIZE)

    return ListPostsResponse(
        data=[PostListItem(**post) for post in paginated_posts],
        pagination=Pagination(page=page, total=total_pages)
    )


@router.get("/posts/{post_id}", response_model=PostDetail)
def get_single_post(post_id: PostId) -> PostDetail:
    """게시글 상세 조회"""
    posts = read_json(settings.posts_file)

    post_index = next((i for i, post in enumerate(posts) if post["id"] == post_id), None)
    if post_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # 조회수 증가
    posts[post_index]["view_count"] = posts[post_index].get("view_count", 0) + 1
    write_json(settings.posts_file, posts)

    return PostDetail(**posts[post_index])


@router.patch("/posts/{post_id}", response_model=PostDetail)
def update_post(author_id: CurrentUserId, post_id: PostId, update_data: PostUpdateRequest) -> PostDetail:
    """게시글 수정"""
    posts = read_json(settings.posts_file)

    post_index = _get_post_index_and_verify_author(posts, post_id, author_id)

    if update_data.title is not None:
        posts[post_index]["title"] = update_data.title
    if update_data.content is not None:
        posts[post_index]["content"] = update_data.content

    posts[post_index]["updated_at"] = datetime.now(UTC).isoformat()

    write_json(settings.posts_file, posts)

    return PostDetail(**posts[post_index])


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(author_id: CurrentUserId, post_id: PostId) -> None:
    """게시글 삭제"""
    posts = read_json(settings.posts_file)

    post_index = _get_post_index_and_verify_author(posts, post_id, author_id)

    posts.pop(post_index)
    write_json(settings.posts_file, posts)
