# utils/database.py

import aiomysql

import json

import logging
from pathlib import Path
from typing import Any, AsyncGenerator

from aiomysql import Cursor
from fastapi import HTTPException, status
from config import settings

pool: aiomysql.Pool | None = None

logger = logging.getLogger(__name__)


def get_pool() -> aiomysql.Pool:
    if pool is None:
        raise RuntimeError("Database pool is not initialized")
    return pool


async def get_cursor() -> AsyncGenerator[Cursor, None]:
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            yield cur


async def init_pool() -> None:
    global pool
    pool = await aiomysql.create_pool(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        db=settings.db_name,
        charset='utf8mb4',
        autocommit=True,
        cursorclass=aiomysql.DictCursor,
        minsize=5,
        maxsize=20,
    )


async def close_pool() -> None:
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()
        pool = None


def read_json(path: Path) -> Any:
    try:
        if not path.exists():
            return []

        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        logger.error("Corrupted JSON file: %s", path, exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing data.",
        ) from e

    except OSError as e:
        logger.error("Failed to read JSON file: %s", path, exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing data.",
        ) from e


def write_json(path: Path, data: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(path)

    except OSError as e:
        logger.error("Failed to write JSON file: %s", path, exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing data.",
        ) from e
