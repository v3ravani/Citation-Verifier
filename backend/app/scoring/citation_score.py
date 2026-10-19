from typing import Optional, Dict, Tuple

def calculate_overall_citation_score(
    metadata_score: float,
    context_similarities: list[float]
) -> Tuple[Optional[float], Dict[str, float]]:
    """
    Combines metadata verification score (55%) and average context semantic similarity (45%).
    If no semantic similarity scores exist, overall score is None (unavailable).
    """
    valid_sims = [s for s in context_similarities if s is not None]

    if not valid_sims:
        # Semantic evidence is unavailable
        return None, {
            "metadata_score": round(metadata_score, 1),
            "semantic_score": 0.0,
            "semantic_available": 0.0,
            "metadata_weight": 1.0,
            "semantic_weight": 0.0
        }

    avg_sim = sum(valid_sims) / len(valid_sims)
    # Scale cosine similarity from [0, 1] to [0, 100] (negative clamped to 0)
    semantic_score_100 = round(max(0.0, avg_sim) * 100.0, 1)

    metadata_comp = round(metadata_score * 0.55, 1)
    semantic_comp = round(semantic_score_100 * 0.45, 1)
    overall = round(min(100.0, metadata_comp + semantic_comp), 1)

    return overall, {
        "metadata_score": round(metadata_score, 1),
        "semantic_score": semantic_score_100,
        "raw_cosine_similarity": round(avg_sim, 3),
        "metadata_component": metadata_comp,
        "semantic_component": semantic_comp,
        "semantic_available": 1.0,
        "metadata_weight": 0.55,
        "semantic_weight": 0.45,
    }
