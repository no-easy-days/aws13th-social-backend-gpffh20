import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, status

from config import settings
from routers.users import CurrentUserId
from schemas.commons import Page, PostId
from schemas.post import ListPostsQuery, PostCreateRequest, PostListItem
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
async def create_post(author_id: CurrentUserId, post: PostCreateRequest):
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


# edit post
@router.patch("/posts/{post_id}")
async def update_post(post_id: PostId):
    return {"success": "update_post"}


# delete post
@router.delete("/posts/{post_id}")
async def delete_post(post_id: PostId):
    return {"success": "delete_post"}
