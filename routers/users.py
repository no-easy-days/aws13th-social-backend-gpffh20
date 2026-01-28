import uuid
from datetime import datetime, UTC, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete

from config import settings
from db.models.user import User
from db.models.user_session import UserSession
from schemas.commons import UserId, DBSession
from schemas.user import (
    UserMyProfile,
    UserUpdateRequest, UserProfile,
    UserCreateRequest, UserCreateResponse, UserLoginRequest, UserLoginResponse,
    TokenRefreshResponse,
)
from utils.auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, DUMMY_HASH, get_current_user_id, hash_token
)

router = APIRouter(
    tags=["USERS"],
)

CurrentUserId = Annotated[str, Depends(get_current_user_id)]
ALLOWED_PROFILE_UPDATE_FIELDS = frozenset(["nickname", "profile_img"])

PROFILE_SET_CLAUSE_MAP = {
    frozenset(["nickname"]): "nickname = %(nickname)s",
    frozenset(["profile_img"]): "profile_img = %(profile_img)s",
    frozenset(["nickname", "profile_img"]): "nickname = %(nickname)s, profile_img = %(profile_img)s",
}


@router.post("/users", response_model=UserCreateResponse,
             status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreateRequest, db: DBSession) -> UserCreateResponse:
    """회원가입"""
    new_user = User(
        id=f"user_{uuid.uuid4().hex}",
        email=user.email,
        nickname=user.nickname,
        password=hash_password(user.password),
        profile_img=user.profile_img,
    )
    db.add(new_user)

    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return UserCreateResponse.model_validate(new_user)


REFRESH_TOKEN_COOKIE_KEY = "refresh_token"


@router.post("/auth/tokens", response_model=UserLoginResponse)
async def get_auth_tokens(
        user: UserLoginRequest,
        request: Request,
        response: Response,
        db: DBSession,
) -> UserLoginResponse:
    """로그인"""
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()

    # 타이밍 공격 방지: 유저 존재 여부와 관계없이 항상 해시 비교 수행
    hashed_password = db_user.password if db_user else DUMMY_HASH
    is_password_correct = verify_password(user.password, hashed_password)

    if db_user is None or not is_password_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # TODO: 오래된 세션 정리 -> 배치 작업 처리

    # 토큰 생성
    token_data = {"sub": db_user.id}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    # 세션 생성
    new_session = UserSession(
        id=f"session_{uuid.uuid4().hex}",
        user_id=db_user.id,
        refresh_token=hash_token(refresh_token),
        device_info=request.headers.get("User-Agent", "Unknown"),
    )

    db.add(new_session)
    await db.flush()

    # Refresh token을 HttpOnly 쿠키로 설정
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/",
    )

    return UserLoginResponse(access_token=access_token)


@router.post("/auth/tokens/refresh", response_model=TokenRefreshResponse)
async def refresh_access_token(
        db: DBSession,
        response: Response,
        refresh_token: str | None = Cookie(None, alias=REFRESH_TOKEN_COOKIE_KEY)
) -> TokenRefreshResponse:
    """Access Token 갱신 (쿠키에서 refresh_token 읽음) + Refresh Token Rotation"""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh token not found",
        )

    payload = decode_token(refresh_token, "refresh")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )

    # DB에서 해당 세션 조회 (해시된 토큰으로 검색)
    hashed_refresh_token = hash_token(refresh_token)
    result = await db.execute(
        select(UserSession).where(UserSession.refresh_token == hashed_refresh_token)
    )
    session = result.scalar_one_or_none()

    if not session:
        # 토큰이 DB에 없음 → 이미 사용된 토큰 (탈취 의심)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )

    # user_id 일치 확인
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )

    # 새 토큰 발급
    token_data = {"sub": user_id}
    new_access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data=token_data)

    # 새 refresh token으로 업데이트 + last_used_at 갱신
    session.refresh_token = hash_token(new_refresh_token)
    now = datetime.now(UTC)
    if now - session.last_used_at > timedelta(hours=1):
        session.last_used_at = now

    # 새 refresh token을 쿠키에 설정 (원본)
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        value=new_refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/",
    )

    return TokenRefreshResponse(access_token=new_access_token)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
        response: Response,
        db: DBSession,
        refresh_token: str | None = Cookie(None, alias=REFRESH_TOKEN_COOKIE_KEY)
) -> None:
    """로그아웃 (refresh_token 쿠키 삭제 + DB 세션 삭제)"""
    if refresh_token:
        # 해당 세션만 삭제
        await db.execute(
            delete(UserSession).where(UserSession.refresh_token == hash_token(refresh_token))
        )
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE_KEY, path="/")


@router.get("/users/me", response_model=UserMyProfile)
async def get_my_profile(user_id: CurrentUserId, db: DBSession) -> UserMyProfile:
    """내 프로필 조회"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserMyProfile.model_validate(user)


@router.patch("/users/me", response_model=UserMyProfile)
async def update_my_profile(user_id: CurrentUserId, update_data: UserUpdateRequest,
                            db: DBSession) -> UserMyProfile:
    """내 프로필 수정"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)

    return UserMyProfile.model_validate(user)


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_specific_user(user_id: UserId, db: DBSession) -> UserProfile:
    """특정 유저 프로필 조회"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserProfile.model_validate(user)


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(user_id: CurrentUserId, db: DBSession) -> None:
    """회원 탈퇴"""
    result = await db.execute(delete(User).where(User.id == user_id))
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
