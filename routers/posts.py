import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, status, HTTPException

from config import settings
from routers.users import CurrentUserId
from schemas.commons import Page, PostId, Pagination, CurrentCursor
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
async def get_posts(cur: CurrentCursor, query: ListPostsQuery = Depends()) -> ListPostsResponse:
    """
    게시글 전체 목록 조회
    - 검색
    - 정렬(조회수, 좋아요수, 최신순)
    - 페이지네이션 (20개씩)
    """
    offset = (query.page - 1) * PAGE_SIZE

    # 검색 조건
    if query.q:
        search_pattern = f"%{query.q}%"
        where_clause = "WHERE title LIKE %s OR content LIKE %s"
        params = (search_pattern, search_pattern)
    else:
        where_clause = ""
        params = ()

    # 총 개수 조회
    await cur.execute(
        f"SELECT COUNT(*) as total FROM posts {where_clause}",
        params
    )
    total_count = (await cur.fetchone())["total"]
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE or 1

    # 게시글 목록 조회
    await cur.execute(
        f"""
        SELECT id, author, title, view_count, like_count, created_at
        FROM posts
        {where_clause}
        ORDER BY {query.sort.value} {query.order.value.upper()}
        LIMIT %s OFFSET %s
        """,
        (*params, PAGE_SIZE, offset)
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
        INSERT INTO posts (id, author_id, title, content, view_count, like_count, created_at, updated_at)
        VALUES (%(id)s, %(author_id)s, %(title)s, %(content)s, %(view_count)s, %(like_count)s, %(created_at)s,
                %(updated_at)s)
        """,
        {
            "id": post_id,
            "author_id": author_id,
            "title": post.title,
            "content": post.content,
            "view_count": 0,
            "like_count": 0,
            "created_at": now,
            "updated_at": now
        }
    )

    new_post_model = PostListItem(
        id=post_id,
        author=author_id,
        title=post.title,
        view_count=0,
        like_count=0,
        created_at=now,
    )

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
