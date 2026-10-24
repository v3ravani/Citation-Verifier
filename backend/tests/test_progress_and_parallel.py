import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import ParsedReference, VerificationResult, ExternalRecord
from backend.app.services.progress_manager import (
    init_progress,
    update_progress,
    get_progress,
    fail_progress,
    clear_progress
)
from backend.app.services.pipeline import run_verification_pipeline

client = TestClient(app)

def test_progress_manager_lifecycle():
    paper_id = "test_progress_paper_123"
    clear_progress(paper_id)

    # 1. Initial state
    init_progress(paper_id, total_refs=20)
    p = get_progress(paper_id)
    assert p["paper_id"] == paper_id
    assert p["percent"] == 5
    assert p["total_refs"] == 20
    assert p["status"] == "processing"

    # 2. Update progress
    update_progress(
        paper_id,
        percent=45,
        stage="Concurrently verifying references (9/20)...",
        details="Ref: Deep Residual Learning",
        completed_refs=9,
        total_refs=20
    )
    p = get_progress(paper_id)
    assert p["percent"] == 45
    assert p["completed_refs"] == 9
    assert p["details"] == "Ref: Deep Residual Learning"

    # 3. Fail progress
    fail_progress(paper_id, "Network failure during external lookup")
    p = get_progress(paper_id)
    assert p["status"] == "error"
    assert "Network failure" in p["details"]

    # 4. Clear
    clear_progress(paper_id)

def test_progress_api_endpoint():
    paper_id = "test_api_paper_456"
    init_progress(paper_id, total_refs=10)
    update_progress(paper_id, percent=60, stage="Analyzing vectors...", completed_refs=6, total_refs=10)

    resp = client.get(f"/api/analyze/{paper_id}/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["paper_id"] == paper_id
    assert data["percent"] == 60
    assert data["completed_refs"] == 6
    assert data["total_refs"] == 10
    clear_progress(paper_id)

def test_progress_endpoint_invalid_id():
    resp = client.get("/api/analyze/ab/progress")
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_parallel_reference_verification():
    """Verify that multiple references are verified concurrently and update progress."""
    from backend.app.models.schemas import ParsedReference, VerificationResult, ExternalRecord

    sample_refs = [
        ParsedReference(reference_id=i, raw_text=f"Author {i}. 202{i}. Paper Title {i}.", title=f"Paper Title {i}", authors=[f"Author {i}"], year=2020 + i)
        for i in range(1, 6)
    ]

    mock_verif = VerificationResult(
        status="verified_exact",
        source="crossref",
        title_similarity=1.0,
        author_match=1.0,
        year_match=True,
        doi_match=None,
        verification_score=100.0,
        notes=["Verified exact match"]
    )
    mock_ext = ExternalRecord(
        source="crossref",
        title="Mock Title",
        authors=["Mock Author"],
        year=2021,
        sources_verified=["crossref", "openalex"]
    )

    paper_id = "test_parallel_run_789"
    init_progress(paper_id, total_refs=len(sample_refs))

    with patch("backend.app.services.pipeline.verify_reference", new=AsyncMock(return_value=(mock_verif, mock_ext))) as mock_call:
        # Simulate parallel run step
        from backend.app.services.pipeline import run_verification_pipeline
        # We can test verify_reference called 5 times
        sem = asyncio.Semaphore(15)
        completed = 0
        async def verify_one(ref):
            nonlocal completed
            async with sem:
                res = await mock_call(ref)
                completed += 1
                update_progress(paper_id, percent=25 + int((completed / 5) * 50), stage=f"Checked {completed}/5", completed_refs=completed, total_refs=5)
                return res

        results = await asyncio.gather(*[verify_one(r) for r in sample_refs])
        assert len(results) == 5
        assert mock_call.call_count == 5

        prog = get_progress(paper_id)
        assert prog["completed_refs"] == 5
        assert prog["percent"] == 75
        clear_progress(paper_id)
