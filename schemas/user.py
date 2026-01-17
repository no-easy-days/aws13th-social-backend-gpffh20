from datetime import datetime
import re

from pydantic import BaseModel, EmailStr, model_validator, StringConstraints, AfterValidator
from typing import Annotated

from schemas.commons import UserId

SPECIAL_CHARS = r"!\"#$%&'()*+,\-./:;<=>?@\[₩\]\^_`{|}~"
_RE_UPPER = re.compile(r"[A-Z]")
_RE_LOWER = re.compile(r"[a-z]")
_RE_DIGIT = re.compile(r"\d")
_RE_SPECIAL = re.compile(rf"[{SPECIAL_CHARS}]")


def validate_password(password: str) -> str:
    if not _RE_UPPER.search(password):
        raise ValueError("비밀번호에 대문자가 포함되어야 합니다")
    if not _RE_LOWER.search(password):
        raise ValueError("비밀번호에 소문자가 포함되어야 합니다")
    if not _RE_DIGIT.search(password):
        raise ValueError("비밀번호에 숫자가 포함되어야 합니다")
    if not _RE_SPECIAL.search(password):
        raise ValueError("비밀번호에 특수문자가 포함되어야 합니다")
    return password


Password = Annotated[
    str,
    StringConstraints(
        min_length=8,
        max_length=16,
    ),
    AfterValidator(validate_password),
]

Nickname = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=10,
        pattern=r"^[A-Za-z0-9]+$",
    ),
]


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: Password
    nickname: Nickname
    profile_img: str | None = None


class UserCreateResponse(BaseModel):
    id: UserId
    nickname: Nickname
    email: EmailStr
    created_at: datetime


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMyProfile(BaseModel):
    id: UserId
    email: EmailStr
    nickname: Nickname
    profile_img: str | None = None
    created_at: datetime


class UserUpdateRequest(BaseModel):
    nickname: Nickname | None = None
    profile_img: str | None = None

    @model_validator(mode='after')
    def check_at_least_one_field(self):
        """
        PATCH 요청에서 "미전송" vs "명시적 null 전송(삭제요청)"을 구분하기 위해
        사용자가 실제로 보낸 필드 집합(model_fields_set)을 기준으로 검사
        """
        if not self.model_fields_set:
            raise ValueError("최소 하나의 필드는 입력 해야 합니다")

        if "nickname" in self.model_fields_set and self.nickname is None:
            raise ValueError("nickname은 null로 설정할 수 없습니다.")
        return self


class UserProfile(BaseModel):
    id: UserId
    nickname: Nickname
    profile_img: str | None = None
