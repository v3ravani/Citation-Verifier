import os
from pathlib import Path

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Storage directories (under project root for unified access or configured)
UPLOADS_DIR = PROJECT_ROOT / "uploads"
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = PROJECT_ROOT / "cache"
CROSSREF_CACHE_DIR = CACHE_DIR / "crossref"
SEMANTIC_SCHOLAR_CACHE_DIR = CACHE_DIR / "semantic_scholar"
EMBEDDINGS_CACHE_DIR = CACHE_DIR / "embeddings"
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"

def ensure_directories():
    """Ensure all required filesystem directories exist."""
    for directory in [
        UPLOADS_DIR,
        DATA_DIR,
        CACHE_DIR,
        CROSSREF_CACHE_DIR,
        SEMANTIC_SCHOLAR_CACHE_DIR,
        EMBEDDINGS_CACHE_DIR,
        RESULTS_DIR,
        LOGS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            try:
                gitkeep.touch()
            except OSError:
                pass
