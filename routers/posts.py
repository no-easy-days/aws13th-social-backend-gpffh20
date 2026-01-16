from fastapi import APIRouter, Depends

from schemas.commons import Page, PostId
from schemas.post import ListPostsQuery

router = APIRouter(
    tags=["POSTS"],
)


# List, search, sort posts
@router.get("/posts")
async def get_posts(query: ListPostsQuery = Depends()):
    return {"success": "get_posts"}


# post new post
@router.post("/posts")
async def create_post(post: dict):
    return {"success": "create_post"}


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
