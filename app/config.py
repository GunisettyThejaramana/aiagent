from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ==========================================================
    # Application
    # ==========================================================
    PROJECT_NAME: str = "Enterprise AI Assistant"

    # ==========================================================
    # PostgreSQL Database
    # ==========================================================
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    # ==========================================================
    # OpenAI
    # ==========================================================
    OPENAI_API_KEY: str

    # ==========================================================
    # Local Document Sources
    # Multiple paths separated by ';' in the .env file
    # Example:
    # LOCAL_DOCUMENT_PATHS=D:\CompanyData;E:\HRDocs;\\Server01\Shared
    # ==========================================================
    LOCAL_DOCUMENT_PATHS: str = ""

    # ==========================================================
    # Supported File Types
    # ==========================================================
    SUPPORTED_FILE_TYPES: list[str] = [
        ".pdf",
        ".docx",
        ".xlsx",
        ".csv",
        ".pptx",
        ".txt",
    ]

    # ==========================================================
    # Maximum file size to process (MB)
    # ==========================================================
    MAX_FILE_SIZE_MB: int = 50

    # ==========================================================
    # PostgreSQL URL
    # ==========================================================
    @property
    def DATABASE_URL(self):
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ==========================================================
    # Return Local Drive Paths as a List
    # ==========================================================
    @property
    def document_paths(self) -> list[str]:
        if not self.LOCAL_DOCUMENT_PATHS:
            return []

        return [
            path.strip()
            for path in self.LOCAL_DOCUMENT_PATHS.split(";")
            if path.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()