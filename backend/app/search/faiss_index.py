import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from backend.app.core.logging_config import logger

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS is not installed; falling back to NumPy dot-product vector search.")

class ReferenceVectorIndex:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.reference_ids: List[int] = []
        self.titles: List[str] = []
        self.vectors: Optional[np.ndarray] = None
        self.faiss_index = None

    def build_index(self, ref_ids: List[int], titles: List[str], vectors: np.ndarray):
        """
        Builds a normalized Inner Product FAISS index from reference embeddings.
        """
        if len(ref_ids) == 0 or vectors is None or len(vectors) == 0:
            return

        self.reference_ids = ref_ids
        self.titles = titles
        self.vectors = vectors.astype(np.float32)

        if FAISS_AVAILABLE:
            try:
                self.faiss_index = faiss.IndexFlatIP(self.dimension)
                self.faiss_index.add(self.vectors)
                logger.info(f"Built FAISS index with {len(ref_ids)} vectors of dim {self.dimension}")
            except Exception as e:
                logger.error(f"Failed to initialize FAISS index: {e}. Falling back to NumPy.")
                self.faiss_index = None

    def search(
        self,
        query_vec: np.ndarray,
        expected_ref_id: int,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Searches the index for the query vector.
        
        Returns:
            {
                "expected_rank": int (1-based),
                "expected_similarity": float,
                "top_alternatives": [{"reference_id": int, "title": str, "similarity": float}],
                "gap_to_top": float
            }
        """
        if self.vectors is None or len(self.reference_ids) == 0:
            return {
                "expected_rank": None,
                "expected_similarity": None,
                "top_alternatives": [],
                "gap_to_top": 0.0
            }

        q = query_vec.astype(np.float32).reshape(1, -1)
        num_candidates = len(self.reference_ids)

        if self.faiss_index is not None:
            # Search all candidates to rank the expected reference
            similarities, indices = self.faiss_index.search(q, num_candidates)
            sims = similarities[0]
            idxs = indices[0]
        else:
            # NumPy dot product
            sims_all = np.dot(self.vectors, q.T).flatten()
            idxs = np.argsort(-sims_all)
            sims = sims_all[idxs]

        expected_rank = None
        expected_sim = None
        ranked_list = []

        for rank, (idx, sim) in enumerate(zip(idxs, sims), start=1):
            if idx < 0 or idx >= len(self.reference_ids):
                continue
            ref_id = self.reference_ids[idx]
            title = self.titles[idx]
            sim_float = round(float(np.clip(sim, -1.0, 1.0)), 3)
            
            ranked_list.append({
                "rank": rank,
                "reference_id": ref_id,
                "title": title,
                "similarity": sim_float
            })

            if ref_id == expected_ref_id and expected_rank is None:
                expected_rank = rank
                expected_sim = sim_float

        # Top alternatives excluding the expected reference
        top_alternatives = [
            {"reference_id": item["reference_id"], "title": item["title"], "similarity": item["similarity"]}
            for item in ranked_list
            if item["reference_id"] != expected_ref_id
        ][:top_k]

        top_score = ranked_list[0]["similarity"] if ranked_list else 0.0
        gap = round(float(top_score - (expected_sim or 0.0)), 3) if expected_sim is not None else 0.0

        return {
            "expected_rank": expected_rank,
            "expected_similarity": expected_sim,
            "top_alternatives": top_alternatives,
            "gap_to_top": gap
        }
