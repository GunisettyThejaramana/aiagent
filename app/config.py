from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # ============================================================
    # APPLICATION
    # ============================================================

    PROJECT_NAME: str = "Enterprise AI Assistant"

    # ============================================================
    # MAIN DATABASE
    # ============================================================

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    # ============================================================
    # OLLAMA
    # ============================================================

    OLLAMA_BASE_URL: str = (
        "http://127.0.0.1:11434"
    )

    OLLAMA_MODEL: str = (
        "qwen3:8b"
    )

    OLLAMA_TIMEOUT: int = 120

    # ============================================================
    # DATABASE ENCRYPTION
    # ============================================================

    DB_ENCRYPTION_KEY: str = ""

    # ============================================================
    # DOCUMENTS
    # ============================================================

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

    # ============================================================
    # DATABASE URL
    # ============================================================

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

    # ============================================================
    # SUPPORTED EXTENSIONS
    # ============================================================

    @property
    def supported_extensions(self):

        return [
            ext.strip().lower()
            for ext in self.SUPPORTED_FILE_TYPES.split(",")
            if ext.strip()
        ]

    # ============================================================
    # LOCAL SCAN PATHS
    # ============================================================

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


# ============================================================
# SETTINGS
# ============================================================

@lru_cache
def get_settings():

    return Settings()


settings = get_settings()