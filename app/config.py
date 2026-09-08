from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    PROJECT_NAME: str = "Enterprise AI Assistant"

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    OPENAI_API_KEY: str



    LLM_MODEL: str = "gpt-4o-mini"

    LLM_TEMPERATURE: float = 0

    LLM_MAX_TOKENS: int = 2000

    # Used to encrypt passwords of additional databases.
    DB_ENCRYPTION_KEY: str = ""

    SUPPORTED_FILE_TYPES: str = (
        ".pdf,"
        ".docx,"
        ".xlsx,"
        ".csv,"
        ".txt,"
        ".json,"
        ".xml,"
        ".pptx,"
        ".html,"
        ".md"
    )

    LOCAL_SCAN_PATHS: str = (
        f"{Path.home() / 'Documents'};"
        f"{Path.home() / 'Desktop'};"
        f"{Path.home() / 'Downloads'}"
    )

    @property
    def DATABASE_URL(self):

        password = quote_plus(
            self.DB_PASSWORD
        )

        return (
            f"postgresql://"
            f"{self.DB_USER}:"
            f"{password}@"
            f"{self.DB_HOST}:"
            f"{self.DB_PORT}/"
            f"{self.DB_NAME}"
            f"?sslmode=require"
        )

    @property
    def supported_extensions(self):

        return [
            ext.strip().lower()
            for ext in self.SUPPORTED_FILE_TYPES.split(",")
            if ext.strip()
        ]

    @property
    def local_scan_paths(self):

        return [
            path.strip()
            for path in self.LOCAL_SCAN_PATHS.split(";")
            if path.strip()
        ]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings():

    return Settings()


settings = get_settings()





