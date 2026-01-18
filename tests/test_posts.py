"""
게시글 API 테스트

실행 방법:
    uv sync --all-extras  # dev 의존성 설치
    pytest tests/test_posts.py -v
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from utils.auth import create_access_token


@pytest.fixture
def client():
    """테스트용 FastAPI 클라이언트"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """인증 헤더 생성"""
    token = create_access_token(data={"sub": "user_00000001"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_posts_data():
    """테스트용 게시글 데이터"""
    return [
        {
            "id": "post_00000001",
            "author": "user_00000001",
            "title": "첫 번째 글",
            "content": "내용1",
            "view_count": 10,
            "like_count": 5,
            "created_at": "2026-01-17T10:00:00+00:00",
            "updated_at": "2026-01-17T10:00:00+00:00",
        },
        {
            "id": "post_00000002",
            "author": "user_00000001",
            "title": "두 번째 글",
            "content": "내용2",
            "view_count": 20,
            "like_count": 10,
            "created_at": "2026-01-17T12:00:00+00:00",
            "updated_at": "2026-01-17T12:00:00+00:00",
        },
        {
            "id": "post_00000003",
            "author": "user_00000002",
            "title": "다른 유저 글",
            "content": "내용3",
            "view_count": 5,
            "like_count": 2,
            "created_at": "2026-01-17T11:00:00+00:00",
            "updated_at": "2026-01-17T11:00:00+00:00",
        },
    ]


class TestGetPostsMine:
    """GET /posts/me 테스트"""

    def test_get_posts_mine_success(self, client, auth_headers, mock_posts_data):
        """내 게시글 목록 조회 성공"""
        with patch("routers.posts.read_json", return_value=mock_posts_data):
            response = client.get("/posts/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2  # user_00000001의 글만
        assert all(p["author"] == "user_00000001" for p in data["data"])

    def test_get_posts_mine_sorted_by_latest(self, client, auth_headers, mock_posts_data):
        """최신순 정렬 확인"""
        with patch("routers.posts.read_json", return_value=mock_posts_data):
            response = client.get("/posts/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # 두 번째 글(12:00)이 첫 번째 글(10:00)보다 먼저
        assert data["data"][0]["id"] == "post_00000002"
        assert data["data"][1]["id"] == "post_00000001"

    def test_get_posts_mine_empty(self, client, auth_headers):
        """게시글 없는 경우"""
        with patch("routers.posts.read_json", return_value=[]):
            response = client.get("/posts/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["total"] == 1

    def test_get_posts_mine_pagination(self, client, auth_headers):
        """페이지네이션 테스트"""
        # 25개 게시글 생성 (PAGE_SIZE=20)
        many_posts = [
            {
                "id": f"post_{i:08d}",
                "author": "user_00000001",
                "title": f"글 {i}",
                "content": f"내용 {i}",
                "view_count": 0,
                "like_count": 0,
                "created_at": f"2026-01-17T{10+i//60:02d}:{i%60:02d}:00+00:00",
                "updated_at": f"2026-01-17T{10+i//60:02d}:{i%60:02d}:00+00:00",
            }
            for i in range(25)
        ]

        with patch("routers.posts.read_json", return_value=many_posts):
            # 1페이지
            response = client.get("/posts/me?page=1", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 20
            assert data["pagination"]["total"] == 2

            # 2페이지
            response = client.get("/posts/me?page=2", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 5

    def test_get_posts_mine_page_overflow(self, client, auth_headers, mock_posts_data):
        """존재하지 않는 페이지 요청 시 마지막 페이지 반환"""
        with patch("routers.posts.read_json", return_value=mock_posts_data):
            response = client.get("/posts/me?page=999", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1  # 마지막 페이지로 조정됨

    def test_get_posts_mine_unauthorized(self, client):
        """인증 없이 요청 시 401"""
        response = client.get("/posts/me")
        assert response.status_code == 401

    def test_get_posts_mine_invalid_token(self, client):
        """잘못된 토큰으로 요청 시 401"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/posts/me", headers=headers)
        assert response.status_code == 401


class TestGetSinglePost:
    """GET /posts/{post_id} 테스트"""

    def test_get_single_post_success(self, client, mock_posts_data):
        """게시글 조회 성공"""
        with patch("routers.posts.read_json", return_value=mock_posts_data):
            with patch("routers.posts.write_json"):
                response = client.get("/posts/post_00000001")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "post_00000001"
        assert data["title"] == "첫 번째 글"
        assert data["content"] == "내용1"

    def test_get_single_post_view_count_increment(self, client, mock_posts_data):
        """조회 시 view_count 증가 확인"""
        original_view_count = mock_posts_data[0]["view_count"]

        with patch("routers.posts.read_json", return_value=mock_posts_data):
            with patch("routers.posts.write_json") as mock_write:
                client.get("/posts/post_00000001")

                # write_json이 호출되었는지 확인
                mock_write.assert_called_once()
                # 저장된 데이터에서 view_count가 증가했는지 확인
                saved_posts = mock_write.call_args[0][1]
                saved_post = next(p for p in saved_posts if p["id"] == "post_00000001")
                assert saved_post["view_count"] == original_view_count + 1

    def test_get_single_post_not_found(self, client):
        """존재하지 않는 게시글 요청 시 404"""
        with patch("routers.posts.read_json", return_value=[]):
            response = client.get("/posts/post_99999999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Post not found"

    def test_get_single_post_legacy_data_without_view_count(self, client):
        """view_count가 없는 레거시 데이터도 기본값 0으로 처리"""
        legacy_post = {
            "id": "post_abcd1234",
            "author": "user_00000001",
            "title": "레거시 글",
            "content": "레거시 내용",
            # view_count, like_count 없음
            "created_at": "2026-01-17T10:00:00+00:00",
            "updated_at": "2026-01-17T10:00:00+00:00",
        }

        with patch("routers.posts.read_json", return_value=[legacy_post]):
            with patch("routers.posts.write_json"):
                response = client.get("/posts/post_abcd1234")

        assert response.status_code == 200
        data = response.json()
        assert data["view_count"] == 1
        assert data["like_count"] == 0
