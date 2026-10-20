import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Citation Verifier"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Uploads
    MAX_PDF_SIZE_MB: int = 30
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]

    # External APIs
    CROSSREF_BASE_URL: str = "https://api.crossref.org"
    CROSSREF_MAILTO: str = "academic-verify@example.org"
    SEMANTIC_SCHOLAR_BASE_URL: str = "https://api.semanticscholar.org/graph/v1"
    SEMANTIC_SCHOLAR_API_KEY: str | None = None
    API_TIMEOUT_SECONDS: float = 12.0

    # Cache
    CACHE_TTL_DAYS: int = 30

    # NLP Model
    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Thresholds
    TITLE_MATCH_THRESHOLD: float = 0.85
    STRONG_CONTEXT_THRESHOLD: float = 0.78
    MODERATE_CONTEXT_THRESHOLD: float = 0.62
    WEAK_CONTEXT_THRESHOLD: float = 0.45
    TOP_K_ALTERNATIVES: int = 3

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:5180", "http://127.0.0.1:5180",
        "http://localhost:3000", "http://127.0.0.1:3000",
        "*"
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
