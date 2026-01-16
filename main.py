from fastapi import FastAPI, Depends

from routers import users, posts, comments
from schemas.commons import PostId, CommentId, Page

app = FastAPI()
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)








# ----- LIKES ----- #

# register like
@app.post("/posts/{post_id}/likes")
async def post_like(post_id: PostId):
    pass


# delete like
@app.delete("/posts/{post_id}/likes")
async def delete_like(post_id: PostId):
    pass


# check like status
@app.get("/posts/{post_id}/likes")
async def get_likes_status(post_id: PostId):
    pass


# post list I liked
@app.get("/posts/liked")
async def get_posts_liked(page: Page):
    pass
