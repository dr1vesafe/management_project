from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str
    DEBUG: bool = True

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432

    SECRET: str

    model_config = SettingsConfigDict(
        env_file = '.env',
        env_file_encoding = 'utf-8'
    )

    @property
    def BASE_DATABASE_URL(self) -> str:
        return (
            f'{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}'
            f'@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )
    
    @property
    def DATABASE_URL(self) -> str:
        """Формирование URL для подключения к базе данных"""
        return f'postgresql+asyncpg://{self.BASE_DATABASE_URL}'
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Формирование URL для использования в миграциях Alembic"""
        return f'postgresql://{self.BASE_DATABASE_URL}'


settings = Settings()
