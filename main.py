import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from routers import users, posts, comments, likes
from utils.database import init_db_pool, close_db_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    yield
    await close_db_pool()


app = FastAPI(lifespan=lifespan)


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
