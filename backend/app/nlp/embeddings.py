import numpy as np
from typing import List, Optional
from backend.app.nlp.model_loader import get_sentence_model
from backend.app.core.logging_config import logger

def generate_embeddings(texts: List[str], batch_size: int = 32) -> Optional[np.ndarray]:
    """
    Generates normalized sentence embeddings for a list of text strings.
    Embeddings are L2-normalized so inner product equals cosine similarity.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)

    model = get_sentence_model()
    if model is None:
        logger.warning("Embedding model is not available.")
        return None

    try:
        # Encode with SentenceTransformers (normalize_embeddings=True calculates L2 norm)
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embeddings.astype(np.float32)
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return None

def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Computes cosine similarity between two 1D normalized vectors.
    """
    dot = np.dot(vec1, vec2)
    # Clamp to [-1.0, 1.0] to prevent floating point out-of-range
    return float(np.clip(dot, -1.0, 1.0))
