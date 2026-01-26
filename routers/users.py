import uuid
from datetime import datetime, UTC
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie, Request
from aiomysql import IntegrityError

from config import settings
from schemas.commons import UserId, CurrentCursor
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
from utils.query import build_set_clause

router = APIRouter(
    tags=["USERS"],
)

CurrentUserId = Annotated[str, Depends(get_current_user_id)]


@router.post("/users", response_model=UserCreateResponse,
             status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreateRequest, cur: CurrentCursor) -> UserCreateResponse:
    """회원가입"""
    new_id = f"user_{uuid.uuid4().hex}"
    now = datetime.now(UTC)

    try:
        await cur.execute(
            """
            INSERT INTO users (id, email, nickname, password, profile_img, created_at)
            VALUES (%(id)s, %(email)s, %(nickname)s, %(password)s, %(profile_img)s, %(created_at)s)
            """,
            {
                "id": new_id,
                "email": user.email,
                "nickname": user.nickname,
                "password": hash_password(user.password),
                "profile_img": user.profile_img,
                "created_at": now,
            }
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return UserCreateResponse(
        id=new_id,
        email=user.email,
        nickname=user.nickname,
        created_at=now,
    )


REFRESH_TOKEN_COOKIE_KEY = "refresh_token"


@router.post("/auth/tokens", response_model=UserLoginResponse)
async def get_auth_tokens(
        user: UserLoginRequest,
        request: Request,
        response: Response,
        cur: CurrentCursor
) -> UserLoginResponse:
    """로그인"""
    await cur.execute(
        "SELECT id, password FROM users WHERE email = %s",
        (user.email,)
    )
    db_user = await cur.fetchone()

    # 타이밍 공격 방지: 유저 존재 여부와 관계없이 항상 해시 비교 수행
    hashed_password = db_user["password"] if db_user else DUMMY_HASH
    is_password_correct = verify_password(user.password, hashed_password)

    if db_user is None or not is_password_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # 토큰 생성
    token_data = {"sub": db_user["id"]}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    # 세션 생성
    session_id = f"sess_{uuid.uuid4().hex}"
    device_info = request.headers.get("User-Agent", "Unknown")

    await cur.execute(
        """
        INSERT INTO user_sessions (id, user_id, refresh_token, device_info)
        VALUES (%(session_id)s, %(user_id)s, %(refresh_token)s, %(device_info)s)
        """,
        {
            "session_id": session_id,
            "user_id": db_user["id"],
            "refresh_token": hash_token(refresh_token),
            "device_info": device_info
        }
    )

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
        cur: CurrentCursor,
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
    hashed_token = hash_token(refresh_token)
    await cur.execute(
        "SELECT id, user_id FROM user_sessions WHERE refresh_token = %s",
        (hashed_token,)
    )
    session = await cur.fetchone()

    if not session:
        # 토큰이 DB에 없음 → 이미 사용된 토큰 (탈취 의심)
        # 해당 유저의 이 세션만 삭제 (세션 ID를 모르므로 user_id 기준으로는 불가)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )

    # user_id 일치 확인
    if session["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )

    # 새 토큰 발급
    token_data = {"sub": user_id}
    new_access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data=token_data)

    # 새 refresh token으로 업데이트 + last_used_at 갱신
    await cur.execute(
        """
        UPDATE user_sessions
        SET refresh_token = %s, last_used_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (hash_token(new_refresh_token), session["id"])
    )

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
        cur: CurrentCursor,
        refresh_token: str | None = Cookie(None, alias=REFRESH_TOKEN_COOKIE_KEY)
) -> None:
    """로그아웃 (refresh_token 쿠키 삭제 + DB 세션 삭제)"""
    if refresh_token:
        # 해당 세션만 삭제
        await cur.execute(
            "DELETE FROM user_sessions WHERE refresh_token = %s",
            (hash_token(refresh_token),)
        )
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE_KEY, path="/")


@router.get("/users/me", response_model=UserMyProfile)
async def get_my_profile(user_id: CurrentUserId, cur: CurrentCursor) -> UserMyProfile:
    """내 프로필 조회"""
    await cur.execute(
        """
        SELECT id, email, nickname, profile_img, created_at
        FROM users
        WHERE id = %s
        """,
        (user_id,)
    )
    user = await cur.fetchone()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserMyProfile(**user)


# SQL Injection 방어: UPDATE 허용 필드 -> DB 컬럼 명시적 매핑
USER_UPDATE_COLUMN_MAP = {
    "nickname": "nickname",
    "profile_img": "profile_img",
}


@router.patch("/users/me", response_model=UserMyProfile)
async def update_my_profile(user_id: CurrentUserId, update_data: UserUpdateRequest,
                            cur: CurrentCursor) -> UserMyProfile:
    """내 프로필 수정"""
    # 먼저 사용자 조회
    await cur.execute(
        "SELECT id, email, nickname, profile_img, created_at FROM users WHERE id = %s",
        (user_id,)
    )
    user = await cur.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 안전한 SET 절 생성
    update_fields = update_data.model_dump(exclude_unset=True)
    set_clause, params = build_set_clause(update_fields, USER_UPDATE_COLUMN_MAP)

    if not set_clause:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    query_params = {**params, "user_id": user_id}

    await cur.execute(
        f"UPDATE users SET {set_clause} WHERE id = %(user_id)s",
        query_params
    )

    if cur.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 조회한 데이터 + 변경값으로 응답
    return UserMyProfile(**{**user, **params})


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_specific_user(user_id: UserId, cur: CurrentCursor) -> UserProfile:
    """특정 유저 프로필 조회"""
    await cur.execute(
        "SELECT id, nickname, profile_img FROM users WHERE id = %s",
        (user_id,)
    )
    user = await cur.fetchone()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserProfile(**user)


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(user_id: CurrentUserId, cur: CurrentCursor) -> None:
    """회원 탈퇴"""
    await cur.execute(
        "DELETE FROM users WHERE id = %s",
        (user_id,)
    )
    if cur.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
