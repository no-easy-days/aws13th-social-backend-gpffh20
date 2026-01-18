from fastapi import FastAPI

from routers import users, posts, comments, likes

app = FastAPI()
app.include_router(users.router)
app.include_router(likes.router)
app.include_router(posts.router)
app.include_router(comments.router)
