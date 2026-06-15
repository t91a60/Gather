from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_user: str = "eventsocial"
    postgres_password: str = "eventsocial_secret"
    postgres_db: str = "eventsocial"
    database_url: str = "postgresql+asyncpg://eventsocial:eventsocial_secret@db:5432/eventsocial"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    jwt_secret_key: str = "change-this-to-a-long-random-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    rate_limit_auth_per_minute: int = 10
    rate_limit_content_per_minute: int = 30

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
