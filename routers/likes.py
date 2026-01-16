from fastapi import APIRouter

from schemas.commons import PostId, Page

router = APIRouter(
    tags=["LIKES"],
)


# post list I liked
@router.get("/posts/liked")
async def get_posts_liked(page: Page):
    return {"success": "get_posts_liked"}


# register like
@router.post("/posts/{post_id}/likes")
async def post_like(post_id: PostId):
    return {"success": "post_like"}


# delete like
@router.delete("/posts/{post_id}/likes")
async def delete_like(post_id: PostId):
    return {"success": "delete_like"}


# check like status
@router.get("/posts/{post_id}/likes")
async def get_likes_status(post_id: PostId):
    return {"success": "get_likes_status"}
