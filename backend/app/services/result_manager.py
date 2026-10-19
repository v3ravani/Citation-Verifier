import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
from backend.app.core.paths import RESULTS_DIR, DATA_DIR, UPLOADS_DIR
from backend.app.models.schemas import AnalysisResult
from backend.app.core.logging_config import logger

def sanitize_paper_id(paper_id: str) -> str:
    """Sanitizes paper ID to prevent path traversal vulnerabilities."""
    cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '', paper_id)
    if not cleaned or len(cleaned) < 4:
        raise ValueError("Invalid paper ID format.")
    return cleaned

def save_analysis_result(paper_id: str, result: AnalysisResult) -> Path:
    """Saves structured AnalysisResult to results/<paper_id>.json."""
    clean_id = sanitize_paper_id(paper_id)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{clean_id}.json"

    data = result.model_dump()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Persisted analysis result to {out_path}")
    return out_path

def get_analysis_result(paper_id: str) -> Optional[Dict[str, Any]]:
    """Loads saved analysis JSON if exists."""
    clean_id = sanitize_paper_id(paper_id)
    result_path = RESULTS_DIR / f"{clean_id}.json"
    if not result_path.exists():
        return None

    try:
        with open(result_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading result for {clean_id}: {e}")
        return None

def save_extracted_text(paper_id: str, full_text: str) -> Path:
    """Saves raw extracted text to data/<paper_id>_text.txt."""
    clean_id = sanitize_paper_id(paper_id)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / f"{clean_id}_text.txt"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    return out_path

def get_extracted_text(paper_id: str) -> Optional[str]:
    """Loads raw extracted text for a paper."""
    clean_id = sanitize_paper_id(paper_id)
    text_path = DATA_DIR / f"{clean_id}_text.txt"
    if not text_path.exists():
        return None

    try:
        with open(text_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading extracted text for {clean_id}: {e}")
        return None
