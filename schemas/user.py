from datetime import datetime

from pydantic import BaseModel, EmailStr, model_validator, StringConstraints
from typing import Annotated

Password = Annotated[
    str,
    StringConstraints(
        pattern=r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!\"#$%&'()*+,\-./:;<=>?@\[₩\]\^_`{|}~])[A-Za-z\d!\"#$%&'()*+,\-./:;<=>?@\[₩\]\^_`{|}~]+$",
        min_length=8,
        max_length=16,
        error_message=(
            "비밀번호는 8~16자이며 영문 대소문자, 숫자, 허용된 특수문자 1개 이상을 포함해야 합니다"
        ),
    ),
]

Nickname = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=10,
        pattern=r"^[A-Za-z0-9]+$",
        error_message="닉네임은 1~10자의 영문 대소문자 및 숫자만 사용할 수 있습니다",
    ),
]


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: Password
    nickname: Nickname
    profile_img: str | None = None


class UserCreateResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nickname: Nickname
    email: EmailStr
    created_at: datetime


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    model_config = {"from_attributes": True}

    access_token: str


class UserMyProfile(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: EmailStr
    nickname: Nickname
    profile_img: str | None = None
    created_at: datetime


class UserUpdateRequest(BaseModel):
    nickname: Nickname | None = None
    profile_img: str | None = None

    @model_validator(mode='after')
    def check_at_least_one_field(self):
        if self.nickname is None and self.profile_img is None:
            raise ValueError("최소 하나의 필드는 입력해야 합니다")
        return self


class UserProfile(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nickname: Nickname
    profile_img: str | None = None
