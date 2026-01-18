from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    secret_key: str
    password_pepper: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cookie_secure: bool = True
    users_file: Path = Path(__file__).resolve().parent / "data/users.json"
    posts_file: Path = Path(__file__).resolve().parent / "data/posts.json"
    comments_file: Path = Path(__file__).resolve().parent / "data/comments.json"
    likes_file: Path = Path(__file__).resolve().parent / "data/likes.json"


settings = Settings()
