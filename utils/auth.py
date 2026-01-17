import hmac
import logging
from datetime import datetime, UTC, timedelta

import bcrypt
import jwt

from config import settings

logger = logging.getLogger(__name__)


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
