from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    

    PROJECT_NAME: str = "Enterprise AI Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False


   
    OPENAI_API_KEY: str

    
    LLM_MODEL: str = "gpt-4o-mini"

   
    LLM_TEMPERATURE: float = 0.2

    
    LLM_MAX_TOKENS: int = 2000


    

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str


    

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

    
    RAG_CHUNK_SIZE: int = 1000

    
    RAG_CHUNK_OVERLAP: int = 200

    
    RAG_TOP_K: int = 5


   

    LOCAL_SCAN_PATHS: str = (
        f"{Path.home() / 'Documents'};"
        f"{Path.home() / 'Desktop'};"
        f"{Path.home() / 'Downloads'}"
    )


    

   
    INDEX_PATH: str = "./storage/index"


    
    MEMORY_WINDOW: int = 10

   
    MEMORY_PATH: str = "./storage/memory"


   
    REPORTS_PATH: str = "./storage/reports"

    
    REPORT_FORMATS: str = "pdf,xlsx"


   
    EMAIL_ENABLED: bool = False


    
    CLOUD_ENABLED: bool = False


    
    ALLOW_WRITE_SQL: bool = False


    
    @property
    def DATABASE_URL(self) -> str:
        password = quote_plus(self.DB_PASSWORD)

        return (
            f"postgresql://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?sslmode=require"
        )


    

    @property
    def supported_extensions(self) -> list[str]:
        return [
            ext.strip().lower()
            for ext in self.SUPPORTED_FILE_TYPES.split(",")
            if ext.strip()
        ]


    
    @property
    def local_scan_paths(self) -> list[str]:
        return [
            path.strip()
            for path in self.LOCAL_SCAN_PATHS.split(";")
            if path.strip()
        ]


    

    @property
    def report_formats(self) -> list[str]:
        return [
            fmt.strip().lower()
            for fmt in self.REPORT_FORMATS.split(",")
            if fmt.strip()
        ]


    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )



@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()