import hmac
import os
import uuid
from datetime import datetime, UTC, timedelta
from pathlib import Path

import bcrypt
import jwt
from fastapi import APIRouter, HTTPException, status

from schemas.commons import UserId
from schemas.user import UserCreateRequest, UserCreateResponse, UserLoginRequest, UserLoginResponse
from utils.data import read_json, write_json

USERS_FILE = Path("data/users.json")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

PEPPER = os.getenv("PASSWORD_PEPPER")
if not PEPPER:
    raise RuntimeError("PASSWORD_PEPPER is not set")

router = APIRouter(
    tags=["USERS"],
)


def _prehash(password: str) -> bytes:
    """
    HMAC-SHA256으로 사전 해싱
    - bcrypt 72바이트 제한 우회
    - PEPPER로 password shucking 공격 방지
    """
    return hmac.new(
        key=PEPPER.encode(),
        msg=password.encode(),
        digestmod="sha256"
    ).hexdigest().encode()

def hash_password(password: str) -> str:
    prehashed = _prehash(password)
    return bcrypt.hashpw(prehashed, bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    prehashed = _prehash(plain_password)
    return bcrypt.checkpw(prehashed, hashed_password.encode())


@router.post("/users", response_model=UserCreateResponse,
             status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreateRequest):
    """회원가입"""
    users = read_json(USERS_FILE)

    # 이메일 중복 확인
    if any(u["email"] == user.email for u in users):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # 새 유저 ID 생성
    new_id = f"user_{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC)

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


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# login
@router.post("/auth/tokens", response_model=UserLoginResponse,
             status_code=status.HTTP_200_OK)
def get_auth_tokens(user: UserLoginRequest):
    """로그인"""
    users = read_json(USERS_FILE)

    # 이메일로 유저 찾기
    db_user = next((u for u in users if u["email"] == user.email), None)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # 비밀번호 검증
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # 토큰 생성
    access_token = create_access_token(data={"sub": db_user["id"]})
    return {"access_token": access_token}


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
