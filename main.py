import asyncio
import logging
from contextlib import asynccontextmanager
from sched import scheduler

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.background import BackgroundScheduler

from config import settings
from routers import users, posts, comments, likes
from db.session import engine
from routers.posts import view_count_scheduler
from utils.database import init_db_pool, close_db_pool
from utils.redis import init_redis_pool, close_redis_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    await init_redis_pool()
    scheduler_task = asyncio.create_task(view_count_scheduler(600))

    yield
    scheduler_task.cancel()
    await close_db_pool()
    await close_redis_pool()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(
        "%s %s - %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )


app.include_router(users.router)
app.include_router(likes.router)
app.include_router(posts.router)
app.include_router(comments.router)
