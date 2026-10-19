import pytest
from backend.app.nlp.overclaim import analyze_claim_strength

def test_overclaim_detection_strong_wording_low_sim():
    sent = "This experiment conclusively demonstrates that our method completely eliminates all errors [1]."
    flag, strength, terms, note = analyze_claim_strength(sent, similarity=0.42)
    assert flag is True
    assert strength == "strong"
    assert len(terms) >= 1
    assert "conclusively" in terms or "completely" in terms or "eliminates" in terms
    assert "Heuristic review flag" in note

def test_overclaim_not_flagged_for_tentative_wording():
    sent = "Our preliminary findings suggest that the approach may correlate with higher efficiency [2]."
    flag, strength, terms, note = analyze_claim_strength(sent, similarity=0.55)
    assert flag is False
    assert strength == "moderate"

def test_overclaim_not_flagged_when_similarity_is_high():
    sent = "Vaswani et al. proves that self-attention mechanisms scale effectively [3]."
    flag, strength, terms, note = analyze_claim_strength(sent, similarity=0.88)
    assert flag is False
    assert strength == "strong"
