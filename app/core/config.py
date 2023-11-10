from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file='../.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    token: str
    redis_host: str
    redis_port: int
    redis_db: int
    postgres_password: str
    postgres_user: str
    postgres_db: str
    postgres_host: str
    postgres_port: int
    echo: bool = True
    reset_frequency: int = 6

settings = Settings()