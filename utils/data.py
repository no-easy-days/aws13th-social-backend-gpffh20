# utils/data.py
""" JSON 파일을 임시 DB처럼 다루기 위한 최소 유틸 """

import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status


def read_json(path: Path) -> Any:
    try:
        if not path.exists():
            return []

        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Corrupted JSON file: {path}",
        )

    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read JSON file: {path} ({e})",
        )


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
            detail=f"Failed to write JSON file: {path} ({e})",
        )
