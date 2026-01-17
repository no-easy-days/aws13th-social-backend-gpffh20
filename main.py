from fastapi import FastAPI

from dotenv import load_dotenv

load_dotenv()

from routers import users, posts, comments, likes

app = FastAPI()
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)
