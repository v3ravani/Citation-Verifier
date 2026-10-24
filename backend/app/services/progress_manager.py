import time
from typing import Dict, Any, Optional

# In-memory store for real-time analysis progress per paper_id
_PROGRESS_STORE: Dict[str, Dict[str, Any]] = {}

def init_progress(paper_id: str, total_refs: int = 0) -> None:
    """Initializes a new analysis progress record."""
    _PROGRESS_STORE[paper_id] = {
        "paper_id": paper_id,
        "percent": 5,
        "stage": "Reading PDF & extracting text structure...",
        "details": "Initializing parsing engine",
        "completed_refs": 0,
        "total_refs": total_refs,
        "status": "processing",
        "updated_at": time.time()
    }

def update_progress(
    paper_id: str,
    percent: int,
    stage: str,
    details: str = "",
    completed_refs: Optional[int] = None,
    total_refs: Optional[int] = None,
    status: str = "processing"
) -> None:
    """Updates an existing progress record."""
    entry = _PROGRESS_STORE.get(paper_id, {
        "paper_id": paper_id,
        "completed_refs": 0,
        "total_refs": 0
    })
    entry["paper_id"] = paper_id
    entry["percent"] = max(0, min(100, int(percent)))
    entry["stage"] = stage
    if details:
        entry["details"] = details
    if completed_refs is not None:
        entry["completed_refs"] = completed_refs
    if total_refs is not None:
        entry["total_refs"] = total_refs
    entry["status"] = status
    entry["updated_at"] = time.time()
    _PROGRESS_STORE[paper_id] = entry

def get_progress(paper_id: str) -> Dict[str, Any]:
    """Retrieves progress. If not in memory, checks if paper is already analyzed on disk."""
    if paper_id in _PROGRESS_STORE:
        return _PROGRESS_STORE[paper_id]

    # Check if analysis result is already cached on disk
    try:
        from backend.app.services.result_manager import get_analysis_result
        result = get_analysis_result(paper_id)
        if result:
            total_refs = len(result.references) if result.references else 0
            return {
                "paper_id": paper_id,
                "percent": 100,
                "stage": "Verification complete. Audit dossier ready.",
                "details": f"{total_refs} references verified across 10 scholarly registries.",
                "completed_refs": total_refs,
                "total_refs": total_refs,
                "status": "completed",
                "updated_at": time.time()
            }
    except Exception:
        pass

    return {
        "paper_id": paper_id,
        "percent": 0,
        "stage": "Queued for processing...",
        "details": "",
        "completed_refs": 0,
        "total_refs": 0,
        "status": "pending",
        "updated_at": time.time()
    }

def fail_progress(paper_id: str, error_msg: str) -> None:
    """Marks progress as failed with error details."""
    entry = _PROGRESS_STORE.get(paper_id, {
        "paper_id": paper_id,
        "completed_refs": 0,
        "total_refs": 0
    })
    entry["status"] = "error"
    entry["details"] = error_msg
    entry["stage"] = "Verification pipeline encountered an error."
    entry["updated_at"] = time.time()
    _PROGRESS_STORE[paper_id] = entry

def clear_progress(paper_id: str) -> None:
    """Clears progress for a paper ID."""
    _PROGRESS_STORE.pop(paper_id, None)
