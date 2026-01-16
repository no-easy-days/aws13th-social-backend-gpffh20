from fastapi import APIRouter

from schemas.commons import UserId

router = APIRouter(
    tags=["USERS"],
)


# signup
@router.post("/users")
async def create_user(user: dict):
    return {"success": "create_user"}


# login
@router.post("/auth/tokens")
async def get_auth_tokens():
    return {"success": "get_auth_tokens"}


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
