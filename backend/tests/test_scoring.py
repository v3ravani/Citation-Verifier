import pytest
from backend.app.scoring.metadata_score import calculate_metadata_score
from backend.app.scoring.citation_score import calculate_overall_citation_score

def test_metadata_score_with_doi():
    # Perfect match with DOI: 35 + 40 + 15 + 10 = 100
    res = calculate_metadata_score(
        doi_match=True,
        title_similarity=1.0,
        author_match=1.0,
        year_match=True,
        doi_present_in_ref=True
    )
    assert res["total_metadata_score"] == 100.0
    assert res["doi_points"] == 35.0

def test_metadata_score_without_doi():
    # Weight redistribution when DOI absent: Title=55, Author=25, Year=20
    res = calculate_metadata_score(
        doi_match=None,
        title_similarity=1.0,
        author_match=1.0,
        year_match=True,
        doi_present_in_ref=False
    )
    assert res["total_metadata_score"] == 100.0
    assert res["doi_points"] == 0.0
    assert res["title_points"] == 55.0

def test_overall_citation_score_with_semantic():
    # 55% metadata (80 * 0.55 = 44), 45% semantic (0.80 * 100 * 0.45 = 36) -> 80.0
    score, breakdown = calculate_overall_citation_score(
        metadata_score=80.0,
        context_similarities=[0.80]
    )
    assert score is not None
    assert score == 80.0
    assert breakdown["semantic_available"] == 1.0

def test_overall_citation_score_unavailable_when_no_semantic():
    score, breakdown = calculate_overall_citation_score(
        metadata_score=95.0,
        context_similarities=[]
    )
    # Must be None, not fabricated!
    assert score is None
    assert breakdown["semantic_available"] == 0.0
