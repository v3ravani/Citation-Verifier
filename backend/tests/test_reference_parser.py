import pytest
from backend.app.citations.reference_parser import (
    split_raw_references,
    extract_reference_title,
    parse_reference,
    parse_all_references,
)

def test_split_ieee_references():
    bib_text = """
    [1] A. Vaswani et al., "Attention is all you need," in NeurIPS, 2017.
    [2] J. Devlin, M. Chang, K. Lee, and K. Toutanova, "BERT: Pre-training of deep bidirectional transformers," in NAACL, 2019.
    [3] T. Brown et al., "Language models are few-shot learners," in NeurIPS, 2020.
    """
    entries = split_raw_references(bib_text)
    assert len(entries) == 3
    assert entries[0][0] == 1
    assert entries[0][1] == "[1]"
    assert "Attention is all you need" in entries[0][2]
    assert entries[1][0] == 2
    assert entries[2][0] == 3

def test_extract_reference_title_quoted():
    raw = '[1] A. Author, "Deep Residual Learning for Image Recognition," in CVPR, 2016.'
    title = extract_reference_title(raw)
    assert title == "Deep Residual Learning for Image Recognition"

def test_parse_reference_full():
    raw = '[1] Y. LeCun, Y. Bengio, and G. Hinton, "Deep learning," Nature, vol. 521, no. 7553, pp. 436-444, 2015. https://doi.org/10.1038/nature14539'
    parsed = parse_reference(1, raw)
    assert parsed.reference_id == 1
    assert parsed.year == 2015
    assert parsed.doi == "10.1038/nature14539"
    assert parsed.title == "Deep learning"
    assert parsed.raw_text == raw
