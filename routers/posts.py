import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, status, HTTPException

from config import settings
from routers.users import CurrentUserId
from schemas.commons import Page, PostId
from schemas.post import ListPostsQuery, PostCreateRequest, PostListItem, PostUpdateRequest
from utils.data import read_json, write_json

router = APIRouter(
    tags=["POSTS"],
)


# List, search, sort posts
@router.get("/posts")
async def get_posts(query: ListPostsQuery = Depends()):
    return {"success": "get_posts"}


@router.post("/posts", response_model=PostListItem,
             status_code=status.HTTP_201_CREATED)
def create_post(author_id: CurrentUserId, post: PostCreateRequest):
    """ 게시글 생성 """
    posts = read_json(settings.posts_file)

    post_id = f"post_{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC)

    new_post = {
        "id": post_id,
        "author": author_id,
        "title": post.title,
        "content": post.content,
        "view_count": 0,
        "like_count": 0,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    posts.append(new_post)
    write_json(settings.posts_file, posts)
    return new_post


# post list I wrote
@router.get("/posts/me")
async def get_posts_mine(page: Page):
    return {"success": "get_posts_mine"}


# get a single post
@router.get("/posts/{post_id}")
async def get_single_post(post_id: PostId):
    return {"success": "get_single_post"}


@router.patch("/posts/{post_id}")
def update_post(author_id: CurrentUserId, post_id: PostId, update_data: PostUpdateRequest):
    """게시글 수정"""
    posts = read_json(settings.posts_file)

    post_index = next((i for i, p in enumerate(posts) if p["id"] == post_id), None)
    if post_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="post not found"
        )
    if posts[post_index]["author"] != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not authorized to update this post"
        )
    if update_data.title is not None:
        posts[post_index]["title"] = update_data.title
    if update_data.content is not None:
        posts[post_index]["content"] = update_data.content

    posts[post_index]["updated_at"] = datetime.now(UTC).isoformat()

    write_json(settings.posts_file, posts)

    return posts[post_index]


# delete post
@router.delete("/posts/{post_id}")
async def delete_post(post_id: PostId):
    return {"success": "delete_post"}
