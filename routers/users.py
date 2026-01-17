import uuid
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException, status

from config import settings
from schemas.commons import UserId
from schemas.user import UserCreateRequest, UserCreateResponse, UserLoginRequest, UserLoginResponse
from utils.auth import hash_password, verify_password, create_access_token, DUMMY_HASH
from utils.data import read_json, write_json

router = APIRouter(
    tags=["USERS"],
)


@router.post("/users", response_model=UserCreateResponse,
             status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreateRequest):
    """회원가입"""
    users = read_json(settings.users_file)

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
    write_json(settings.users_file, users)

    return {
        "id": new_id,
        "email": user.email,
        "nickname": user.nickname,
        "created_at": now.isoformat(),
    }


# login
@router.post("/auth/tokens", response_model=UserLoginResponse,
             status_code=status.HTTP_200_OK)
def get_auth_tokens(user: UserLoginRequest):
    """로그인"""
    users = read_json(settings.users_file)

    # 이메일로 유저 찾기
    db_user = next((u for u in users if u["email"] == user.email), None)

    # 타이밍 공격 방지: 유저 존재 여부와 관계없이 항상 해시 비교 수행
    hashed_password = db_user["password"] if db_user else DUMMY_HASH
    is_password_correct = verify_password(user.password, hashed_password)

    if not db_user or not is_password_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # 토큰 생성
    access_token = create_access_token(data={"sub": db_user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}


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
