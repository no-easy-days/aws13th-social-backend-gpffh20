"""테스트 데이터 생성 스크립트

사용법:
    python scripts/seed.py

테스트 계정:
    - email: test@example.com
    - password: Test1234!
"""
import sys
from datetime import datetime, UTC
from pathlib import Path
import json

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.auth import hash_password

DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
POSTS_FILE = DATA_DIR / "posts.json"
COMMENTS_FILE = DATA_DIR / "comments.json"
LIKES_FILE = DATA_DIR / "likes.json"

# 테스트 계정 (평문 비밀번호)
TEST_USERS = [
    {
        "id": "user_test0001",
        "email": "test@example.com",
        "password": "Test1234!",
        "nickname": "TestUser",
        "profile_img": None,
    },
    {
        "id": "user_test0002",
        "email": "test2@example.com",
        "password": "Test1234!",
        "nickname": "TestUser2",
        "profile_img": None,
    },
]


def seed_users():
    """유저 데이터 생성"""
    users = []
    for user in TEST_USERS:
        users.append({
            "id": user["id"],
            "email": user["email"],
            "nickname": user["nickname"],
            "password": hash_password(user["password"]),
            "profile_img": user["profile_img"],
            "created_at": datetime.now(UTC).isoformat(),
        })
    return users


def seed():
    """모든 테스트 데이터 생성"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Users
    users = seed_users()
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

    # 빈 데이터 파일들
    for file in [POSTS_FILE, COMMENTS_FILE, LIKES_FILE]:
        with open(file, "w", encoding="utf-8") as f:
            json.dump([], f)

    print("✅ 테스트 데이터 생성 완료!")
    print(f"\n📁 저장 위치: {DATA_DIR}")
    print("\n👤 테스트 계정:")
    for user in TEST_USERS:
        print(f"   - email: {user['email']}")
        print(f"     password: {user['password']}")
        print()


if __name__ == "__main__":
    seed()
