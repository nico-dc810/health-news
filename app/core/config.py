from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "大健康内容增长大脑"
    app_env: str = "development"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./health_media.db"
    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_model: str = ""
    intelligence_auto_crawl_enabled: bool = True
    intelligence_auto_crawl_workspace_id: str = "demo-workspace"
    intelligence_auto_crawl_interval_hours: int = 24
    intelligence_auto_crawl_max_sources: int = 20
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "health-media"
    secret_key: str = "change-me-in-production-use-env-var"
    cors_origins: str = "https://nico-dc810.github.io,http://localhost:8000,http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
