from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CareerCast"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    frontend_origin: str = "http://127.0.0.1:5500"
    supabase_url: str
    supabase_anon_key: str
    database_url: str = "sqlite:///./careercast.db"
    max_resume_size_mb: int = 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def supabase_user_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1/user"


@lru_cache
def get_settings() -> Settings:
    return Settings()
