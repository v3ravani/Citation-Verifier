import threading
from typing import Optional, Any
from backend.app.core.config import settings
from backend.app.core.logging_config import logger

_model_lock = threading.Lock()
_sentence_model: Optional[Any] = None
_model_load_attempted: bool = False
_model_load_error: Optional[str] = None

def get_sentence_model() -> Optional[Any]:
    """
    Returns the loaded SentenceTransformer model singleton.
    Loads on first call and caches in memory.
    """
    global _sentence_model, _model_load_attempted, _model_load_error

    if _sentence_model is not None:
        return _sentence_model

    with _model_lock:
        if _sentence_model is not None:
            return _sentence_model

        if _model_load_attempted and _model_load_error:
            logger.warning(f"Previous model load failed: {_model_load_error}")
            return None

        _model_load_attempted = True
        try:
            logger.info(f"Loading local sentence embedding model: {settings.MODEL_NAME}")
            from sentence_transformers import SentenceTransformer
            _sentence_model = SentenceTransformer(settings.MODEL_NAME)
            logger.info(f"Successfully loaded {settings.MODEL_NAME}")
            return _sentence_model
        except Exception as e:
            _model_load_error = str(e)
            logger.error(f"Failed to load sentence model {settings.MODEL_NAME}: {e}")
            return None

def is_model_loaded() -> bool:
    return _sentence_model is not None
