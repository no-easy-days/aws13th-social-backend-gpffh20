from dotenv import load_dotenv
from fastapi import FastAPI

from routers import users, posts, comments, likes
from dotenv import load_dotenv

load_dotenv()

load_dotenv()

app = FastAPI()
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)
