import hmac
import logging
from datetime import datetime, UTC, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings

logger = logging.getLogger(__name__)

# Bearer 토큰 인증 스키마
security = HTTPBearer()


def _prehash(password: str) -> bytes:
    """
    HMAC-SHA256으로 사전 해싱
    - bcrypt 72바이트 제한 우회
    - PEPPER로 password shucking 공격 방지
    """
    return hmac.new(
        key=settings.password_pepper.encode(),
        msg=password.encode(),
        digestmod="sha256"
    ).hexdigest().encode()


def hash_password(password: str) -> str:
    prehashed = _prehash(password)
    return bcrypt.hashpw(prehashed, bcrypt.gensalt()).decode()


# 타이밍 공격 방지용 더미 해시
DUMMY_HASH = hash_password("dummy_password_for_timing_attack_prevention")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    prehashed = _prehash(plain_password)
    try:
        return bcrypt.checkpw(prehashed, hashed_password.encode())
    except ValueError:
        logger.warning("Invalid hash format detected")
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """token decoding"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token is expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )


def get_current_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """현재 로그인한 유저 ID 반환"""
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )
    return user_id
