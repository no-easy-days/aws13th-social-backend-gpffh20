import uuid
from datetime import datetime, UTC
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Response

from config import settings
from schemas.commons import UserId
from schemas.user import (
    UserMyProfile,
    UserUpdateRequest, UserProfile,
)
from schemas.user import UserCreateRequest, UserCreateResponse, UserLoginRequest, UserLoginResponse
from utils.auth import hash_password, verify_password, create_access_token, DUMMY_HASH, get_current_user_id
from utils.data import read_json, write_json

router = APIRouter(
    tags=["USERS"],
)

# 의존성 주입용 타입 별칭
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


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


@router.post("/auth/tokens", response_model=UserLoginResponse)
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


@router.get("/users/me", response_model=UserMyProfile)
def get_my_profile(user_id: CurrentUserId):
    """내 프로필 조회"""
    users = read_json(settings.users_file)

    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.patch("/users/me", response_model=UserMyProfile)
def update_my_profile(user_id: CurrentUserId, update_data: UserUpdateRequest):
    """내 프로필 수정"""
    users = read_json(settings.users_file)

    user_index = next((i for i, u in enumerate(users) if u["id"] == user_id), None)
    if user_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 변경할 필드만 업데이트
    update_field = update_data.model_dump(exclude_unset=True)
    users[user_index].update(update_field)

    write_json(settings.users_file, users)

    return users[user_index]


@router.get("/users/{user_id}", response_model=UserProfile)
def get_specific_user(user_id: UserId):
    """특정 유저 프로필 조회"""
    users = read_json(settings.users_file)

    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


# TODO: user 관련 댓글, 게시글, 좋아요 같이 삭제하기
@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(user_id: CurrentUserId):
    """회원 탈퇴"""
    users = read_json(settings.users_file)

    user_index = next((i for i, u in enumerate(users) if u["id"] == user_id), None)
    if user_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    users.pop(user_index)
    write_json(settings.users_file, users)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
