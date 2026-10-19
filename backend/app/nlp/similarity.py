from typing import Optional, Tuple
from backend.app.core.config import settings

def classify_semantic_similarity(similarity: Optional[float]) -> Tuple[str, str]:
    """
    Classifies a cosine similarity score into a research-integrity relevance category.
    Returns: (classification_label, human_readable_explanation)
    """
    if similarity is None:
        return (
            "unavailable",
            "No abstract was available for the cited reference to perform semantic relevance verification."
        )

    sim = round(similarity, 3)

    if sim >= settings.STRONG_CONTEXT_THRESHOLD:
        return (
            "strongly_related",
            f"The citation context demonstrates strong semantic alignment ({sim}) with the cited work's abstract."
        )
    elif sim >= settings.MODERATE_CONTEXT_THRESHOLD:
        return (
            "moderately_related",
            f"The citation context shows moderate topical relevance ({sim}) to the cited abstract."
        )
    elif sim >= settings.WEAK_CONTEXT_THRESHOLD:
        return (
            "weakly_related",
            f"The citation context exhibits weak semantic correspondence ({sim}) with the cited abstract; review recommended."
        )
    else:
        return (
            "likely_unrelated",
            f"The citation context has low semantic similarity ({sim}) with the cited abstract; potential mismatch or tangential citation."
        )
