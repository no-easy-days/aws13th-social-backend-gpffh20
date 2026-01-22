# utils/database.py

import aiomysql

import json

from pathlib import Path
from typing import Any, AsyncGenerator

from aiomysql import Cursor
from fastapi import HTTPException, status
from config import settings

db_pool: aiomysql.Pool | None = None


def get_db_pool() -> aiomysql.Pool:
    if db_pool is None:
        raise RuntimeError("Database db_pool is not initialized")
    return db_pool


async def get_cursor() -> AsyncGenerator[Cursor, None]:
    pool = get_db_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                yield cur
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise


async def init_db_pool() -> None:
    global db_pool
    db_pool = await aiomysql.create_pool(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        db=settings.db_name,
        charset='utf8mb4',
        autocommit=False,
        cursorclass=aiomysql.DictCursor,
        minsize=2,
        maxsize=10,
    )


async def close_db_pool() -> None:
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()
        db_pool = None


def read_json(path: Path) -> Any:
    try:
        if not path.exists():
            return []

        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing data.",
        ) from e

    except OSError as e:
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while processing data.",
        ) from e
