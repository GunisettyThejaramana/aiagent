from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise AI Assistant"

    # Database
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    # OpenAI
    OPENAI_API_KEY: str

    # Supported File Types
    SUPPORTED_FILE_TYPES: str = ".pdf,.docx,.xlsx,.csv,.txt"

    @property
    def DATABASE_URL(self):
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def supported_extensions(self):
        return [
            ext.strip().lower()
            for ext in self.SUPPORTED_FILE_TYPES.split(",")
        ]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()