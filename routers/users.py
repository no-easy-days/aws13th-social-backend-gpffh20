import hashlib
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
from fastapi import APIRouter, HTTPException, status

from schemas.commons import UserId
from schemas.user import UserCreateRequest, UserCreateResponse
from utils.data import read_json, write_json

USERS_FILE = Path("data/users.json")

router = APIRouter(
    tags=["USERS"],
)


def hash_password(password: str) -> str:
    # SHA-256으로 사전 해싱 (bcrypt 72바이트 제한 우회)
    prehashed = hashlib.sha256(password.encode()).hexdigest().encode()
    return bcrypt.hashpw(prehashed, bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    prehashed = hashlib.sha256(plain_password.encode()).hexdigest().encode()
    return bcrypt.checkpw(prehashed, hashed_password.encode())


@router.post("/users", response_model=UserCreateResponse)
async def create_user(user: UserCreateRequest):
    """회원가입"""
    users = read_json(USERS_FILE)

    # 이메일 중복 확인
    if any(u["email"] == user.email for u in users):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # 새 유저 ID 생성
    new_id = f"user_{len(users) + 1}"
    now = datetime.now(timezone.utc)

    new_user = {
        "id": new_id,
        "email": user.email,
        "nickname": user.nickname,
        "password": hash_password(user.password),
        "profile_img": user.profile_img,
        "created_at": now.isoformat(),
    }

    users.append(new_user)
    write_json(USERS_FILE, users)

    return {
        "id": new_id,
        "email": user.email,
        "nickname": user.nickname,
        "created_at": now.isoformat(),
    }


# login
@router.post("/auth/tokens")
async def get_auth_tokens():
    return {"success": "get_auth_tokens"}


# edit profile
# Depends를 활용한 의존성 주입으로 구현
@router.patch("/users/me")
async def update_my_profile():
    return {"success": "update_my_profile"}


# get my profile
# Depends를 활용한 의존성 주입으로 구현
@router.get("/users/me")
async def get_my_profile():
    return {"success": "get_my_profile"}


# delete account
# Depends를 활용한 의존성 주입으로 구현
@router.delete("/users/me")
async def delete_my_account():
    return {"success": "delete_user"}


# get a specific user
@router.get("/users/{user_id}")
async def get_specific_user(user_id: UserId):
    return {"user_id": user_id}
