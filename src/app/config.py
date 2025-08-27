from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str
    DEBUG: bool = True

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432

    SECRET: str

    @property
    def DATABASE_URL(self) -> str:
        """Формирование URL для подключения к базе данных"""
        return (
            f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}'
            f'@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
