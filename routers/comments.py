from fastapi import APIRouter

from schemas.commons import PostId, Page, CommentId

router = APIRouter()


# List all comments for a post
@router.get("/posts/{post_id}/comments")
async def get_comments(post_id: PostId, page: Page):
    return {"success": "get_comments"}


# post comment
@router.post("/posts/{post_id}/comments")
async def post_comment(post_id: PostId):
    return {"success": "post_comments"}


# edit comment
@router.patch("/posts/{post_id}/comments/{comment_id}")
async def update_comment(post_id: PostId, comment_id: CommentId):
    return {"success": "update_comment"}


# delete comment
@router.delete("/posts/{post_id}/comments/{comment_id}")
async def delete_comment(post_id: PostId, comment_id: CommentId):
    return {"success": "delete_comment"}


# comment list I wrote
@router.get("/comments/me")
async def get_comments_mine(page: Page):
    return {"success": "get_comments_mine"}
