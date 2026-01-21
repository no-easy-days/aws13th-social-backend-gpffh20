import uuid
from datetime import datetime, UTC
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie

from config import settings
from schemas.commons import UserId, DbCursor
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


@router.post("/users", response_model=UserCreateResponse,
             status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreateRequest, cur: DbCursor) -> UserCreateResponse:
    """회원가입"""
    new_id = f"user_{uuid.uuid4().hex}"
    now = datetime.now(UTC)

    # 이메일 중복 확인
    await cur.execute(
        "SELECT 1 FROM users WHERE email = %s",
        (user.email,),
    )
    if await cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
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

    return UserCreateResponse(
        id=new_id,
        email=user.email,
        nickname=user.nickname,
        created_at=now,
    )


REFRESH_TOKEN_COOKIE_KEY = "refresh_token"


@router.post("/auth/tokens", response_model=UserLoginResponse)
async def get_auth_tokens(user: UserLoginRequest, response: Response, cur: DbCursor) -> UserLoginResponse:
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

    # Refresh token을 해싱해서 DB에 저장
    await cur.execute(
        "UPDATE users SET refresh_token = %s WHERE id = %s",
        (hash_token(refresh_token), db_user["id"])
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
        cur: DbCursor,
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

    # DB에서 저장된 refresh token 조회
    await cur.execute(
        "SELECT refresh_token FROM users WHERE id = %s",
        (user_id,)
    )
    db_user = await cur.fetchone()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )

    # 저장된 토큰과 비교
    if db_user["refresh_token"] != hash_token(refresh_token):
        # 탈취 의심 → 토큰 무효화
        await cur.execute(
            "UPDATE users SET refresh_token = NULL WHERE id = %s",
            (user_id,)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token reuse detected",
        )

    # 새 토큰 발급
    token_data = {"sub": user_id}
    new_access_token = create_access_token(data=token_data)
    new_refresh_token = create_refresh_token(data=token_data)

    # 새 refresh token을 해싱해서 DB에 저장
    await cur.execute(
        "UPDATE users SET refresh_token = %s WHERE id = %s",
        (hash_token(new_refresh_token), user_id)
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
async def logout(user_id: CurrentUserId, response: Response, cur: DbCursor) -> None:
    """로그아웃 (refresh_token 쿠키 삭제 + DB 토큰 무효화)"""
    # DB에서 refresh token 삭제
    await cur.execute(
        "UPDATE users SET refresh_token = NULL WHERE id = %s",
        (user_id,)
    )
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE_KEY, path="/")


@router.get("/users/me", response_model=UserMyProfile)
async def get_my_profile(user_id: CurrentUserId, cur: DbCursor) -> UserMyProfile:
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


ALLOWED_UPDATE_COLUMNS = frozenset({"nickname", "profile_img"})


@router.patch("/users/me", response_model=UserMyProfile)
async def update_my_profile(user_id: CurrentUserId, update_data: UserUpdateRequest, cur: DbCursor) -> UserMyProfile:
    """내 프로필 수정"""
    # 전달된 필드만 추출
    update_fields = update_data.model_dump(exclude_unset=True)
    update_fields = {k: v for k, v in update_fields.items() if k in ALLOWED_UPDATE_COLUMNS}

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    # 동적 SET 절 생성: "nickname = %(nickname)s, profile_img = %(profile_img)s"
    set_clause = ", ".join(f"{key} = %({key})s" for key in update_fields)
    update_fields["user_id"] = user_id

    await cur.execute(
        f"UPDATE users SET {set_clause} WHERE id = %(user_id)s",
        update_fields
    )

    if cur.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 수정된 데이터 조회
    await cur.execute(
        "SELECT id, email, nickname, profile_img, created_at FROM users WHERE id = %s",
        (user_id,)
    )
    user = await cur.fetchone()

    return UserMyProfile(**user)


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_specific_user(user_id: UserId, cur: DbCursor) -> UserProfile:
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
async def delete_my_account(user_id: CurrentUserId, cur: DbCursor) -> None:
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
