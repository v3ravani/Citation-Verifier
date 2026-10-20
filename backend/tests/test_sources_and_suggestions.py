import pytest
import xml.etree.ElementTree as ET
from backend.app.metadata.arxiv import extract_arxiv_id, parse_arxiv_entry, ATOM_NS
from backend.app.metadata.openalex import reconstruct_openalex_abstract, parse_openalex_work
from backend.app.metadata.europe_pmc import parse_europe_pmc_item
from backend.app.metadata.dblp import parse_dblp_hit
from backend.app.metadata.datacite import parse_datacite_work
from backend.app.services.citation_suggester import (
    format_ieee,
    format_apa,
    format_bibtex,
    extract_search_terms,
    suggest_citations_for_paragraph,
    detect_citation_gaps_in_text,
)
from backend.app.services.report_generator import (
    generate_bibtex_export,
    generate_csv_export,
    generate_markdown_report,
)
from backend.app.services.pdf_annotator import generate_annotated_pdf
from backend.app.models.schemas import AnalysisResult
from backend.app.services.result_manager import get_analysis_result

def test_extract_arxiv_id():
    assert extract_arxiv_id("Attention Is All You Need arXiv:1706.03762v5 [cs.CL]") == "1706.03762v5"
    assert extract_arxiv_id("Paper preprint at 2103.00020") == "2103.00020"
    assert extract_arxiv_id("arxiv: 1409.0473") == "1409.0473"
    assert extract_arxiv_id("Standard nature paper without preprint") is None

def test_parse_arxiv_entry():
    sample_xml = """<entry xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
        <id>http://arxiv.org/abs/1706.03762v1</id>
        <title> Attention Is All You Need </title>
        <summary> The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. </summary>
        <published>2017-06-12T17:57:34Z</published>
        <author><name>Ashish Vaswani</name></author>
        <author><name>Noam Shazeer</name></author>
        <arxiv:doi>10.5555/3295222.3295349</arxiv:doi>
    </entry>"""
    root = ET.fromstring(sample_xml)
    parsed = parse_arxiv_entry(root)
    assert parsed["title"] == "Attention Is All You Need"
    assert parsed["year"] == 2017
    assert len(parsed["authors"]) == 2
    assert "Ashish Vaswani" in parsed["authors"]
    assert parsed["venue"] == "arXiv Preprint"
    assert "recurrent or convolutional" in parsed["abstract"]

def test_reconstruct_openalex_abstract():
    inverted = {
        "Attention": [0],
        "is": [1],
        "all": [2],
        "you": [3],
        "need": [4]
    }
    reconstructed = reconstruct_openalex_abstract(inverted)
    assert reconstructed == "Attention is all you need"
    assert reconstruct_openalex_abstract(None) is None

def test_parse_openalex_work():
    raw_work = {
        "title": "Deep Learning",
        "publication_year": 2015,
        "doi": "https://doi.org/10.1038/nature14539",
        "authorships": [
            {"author": {"display_name": "Yann LeCun"}},
            {"author": {"display_name": "Yoshua Bengio"}},
            {"author": {"display_name": "Geoffrey Hinton"}},
        ],
        "primary_location": {
            "source": {"display_name": "Nature"},
            "landing_page_url": "https://www.nature.com/articles/nature14539"
        },
        "cited_by_count": 55000,
        "abstract_inverted_index": {
            "Deep": [0],
            "learning": [1],
            "allows": [2],
            "computational": [3],
            "models": [4]
        }
    }
    parsed = parse_openalex_work(raw_work)
    assert parsed["title"] == "Deep Learning"
    assert parsed["year"] == 2015
    assert parsed["doi"] == "10.1038/nature14539"
    assert len(parsed["authors"]) == 3
    assert parsed["venue"] == "Nature"
    assert parsed["citation_count"] == 55000
    assert "Deep learning allows" in parsed["abstract"]

def test_parse_europe_pmc_item():
    normal_item = {
        "title": "CRISPR-Cas9 structures and mechanisms",
        "authorString": "Doudna JA, Charpentier E",
        "pubYear": "2014",
        "journalTitle": "Science",
        "doi": "10.1126/science.1258096",
        "abstractText": "The RNA-guided Cas9 endonuclease uses RNA-DNA base pairing to target double-strand breaks.",
        "citedByCount": 8500,
        "isRetracted": "N"
    }
    parsed = parse_europe_pmc_item(normal_item)
    assert parsed["title"] == "CRISPR-Cas9 structures and mechanisms"
    assert parsed["year"] == 2014
    assert len(parsed["authors"]) == 2
    assert parsed["doi"] == "10.1126/science.1258096"
    assert parsed["is_retracted"] is False

    retracted_item = {
        "title": "Retracted: Falsified clinical trial analysis",
        "authorString": "Fraudster A",
        "pubYear": "2020",
        "isRetracted": "Y"
    }
    parsed_retracted = parse_europe_pmc_item(retracted_item)
    assert parsed_retracted["is_retracted"] is True

def test_parse_dblp_hit():
    dblp_hit = {
        "info": {
            "title": "Deep Residual Learning for Image Recognition.",
            "authors": {
                "author": [
                    {"text": "Kaiming He"},
                    {"text": "Xiangyu Zhang"},
                    {"text": "Shaoqing Ren"},
                    {"text": "Jian Sun"}
                ]
            },
            "year": "2016",
            "venue": "CVPR",
            "doi": "10.1109/CVPR.2016.90",
            "ee": "https://doi.org/10.1109/CVPR.2016.90"
        }
    }
    parsed = parse_dblp_hit(dblp_hit)
    assert parsed["title"] == "Deep Residual Learning for Image Recognition"
    assert parsed["year"] == 2016
    assert len(parsed["authors"]) == 4
    assert "Kaiming He" in parsed["authors"]
    assert parsed["doi"] == "10.1109/cvpr.2016.90"
    assert parsed["source"] == "dblp"

def test_parse_datacite_work():
    datacite_item = {
        "attributes": {
            "titles": [{"title": "ImageNet Large Scale Visual Recognition Challenge Dataset"}],
            "creators": [{"name": "Olga Russakovsky"}, {"name": "Jia Deng"}],
            "publicationYear": 2015,
            "doi": "10.1007/s11263-015-0816-y",
            "publisher": "Springer",
            "descriptions": [{"description": "The ImageNet dataset evaluation benchmark."}]
        }
    }
    parsed = parse_datacite_work(datacite_item)
    assert "ImageNet Large Scale" in parsed["title"]
    assert parsed["year"] == 2015
    assert len(parsed["authors"]) == 2
    assert parsed["doi"] == "10.1007/s11263-015-0816-y"
    assert parsed["source"] == "datacite"

def test_citation_formatters():
    authors = ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"]
    title = "Attention is all you need"
    venue = "Advances in Neural Information Processing Systems"
    year = 2017
    doi = "10.5555/3295222.3295349"

    ieee = format_ieee(authors, title, venue, year, doi)
    assert "A. Vaswani et al." in ieee
    assert '"Attention is all you need"' in ieee
    assert "2017" in ieee

    apa = format_apa(authors, title, venue, year, doi)
    assert "Vaswani, A." in apa
    assert "(2017)" in apa

    bibtex = format_bibtex(authors, title, venue, year, doi)
    assert "@inproceedings{" in bibtex
    assert "vaswani2017attention" in bibtex
    assert "title = {{Attention is all you need}}" in bibtex

def test_extract_search_terms():
    sentence = "We show that convolutional networks conclusively outperform older recurrent neural networks on image classification."
    terms = extract_search_terms(sentence)
    assert "convolutional" in terms.lower()
    assert "networks" in terms.lower()
    assert "classification" in terms.lower()
    assert "that" not in terms.split()
    assert "we" not in terms.split()

@pytest.mark.asyncio
async def test_citation_suggester_empty():
    res = await suggest_citations_for_paragraph("   ")
    assert res.claims_analyzed == 0
    assert len(res.results) == 0

@pytest.mark.asyncio
async def test_detect_citation_gaps_in_text():
    sample_doc = """
    In recent years, deep neural architectures have revolutionized computational vision.
    Studies show that self-attention mechanisms significantly improve machine translation quality across benchmarks.
    However, conventional convolutional networks [1] require extensive spatial convolutions.
    """
    gaps = await detect_citation_gaps_in_text(sample_doc, max_gaps=2)
    assert gaps.total_gaps_detected >= 1
    # Check that the detected gap is the uncited sentence
    first_gap = gaps.gaps[0]
    assert "self-attention" in first_gap.sentence or "computational vision" in first_gap.sentence
    assert "[1]" not in first_gap.sentence

def test_annotated_pdf_generation_content():
    loaded = get_analysis_result("eb774d3c80ab6663")
    assert loaded is not None
    out_pdf = generate_annotated_pdf("eb774d3c80ab6663", loaded)
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 5000

def test_exports_bibtex_csv_markdown():
    loaded = get_analysis_result("eb774d3c80ab6663")
    assert loaded is not None
    res = AnalysisResult.model_validate(loaded)

    bibtex = generate_bibtex_export(res)
    assert "@" in bibtex
    assert "author =" in bibtex
    assert "title =" in bibtex

    csv_data = generate_csv_export(res)
    assert "Reference_ID" in csv_data
    assert "Integrity_Score" in csv_data
    assert "Verification_Status" in csv_data

    md_report = generate_markdown_report(res)
    assert "# Citation Verification" in md_report
    assert "Executive Summary" in md_report
    assert "Reference Verification Table" in md_report

def test_parse_pubmed_summary():
    from backend.app.metadata.pubmed import parse_pubmed_summary
    sample_summary = {
        "title": "SARS-CoV-2 Spike Protein Structure and Evolution",
        "authors": [{"name": "Walls AC"}, {"name": "Park YJ"}],
        "pubdate": "2020 Mar 9",
        "source": "Cell",
        "articleids": [{"idtype": "doi", "value": "10.1016/j.cell.2020.02.058"}, {"idtype": "pubmed", "value": "32155444"}],
        "pubtype": ["Journal Article"],
        "nlmuniqueid": "0413066"
    }
    parsed = parse_pubmed_summary("32155444", sample_summary)
    assert parsed["title"] == "SARS-CoV-2 Spike Protein Structure and Evolution"
    assert parsed["year"] == 2020
    assert len(parsed["authors"]) == 2
    assert parsed["doi"] == "10.1016/j.cell.2020.02.058"
    assert parsed["is_medline_indexed"] is True
    assert parsed["is_retracted"] is False
    assert parsed["source"] == "pubmed"

def test_parse_doaj_article():
    from backend.app.metadata.doaj import parse_doaj_article
    sample_item = {
        "bibjson": {
            "title": "Open Access Transformer Models for Low-Resource Languages",
            "author": [{"name": "Maria Garcia"}, {"name": "Luca Rossi"}],
            "year": "2023",
            "journal": {"title": "Journal of Machine Learning Research"},
            "identifier": [{"type": "doi", "id": "10.5555/jmlr.2023.01"}],
            "abstract": "We present open transformer architectures evaluated on twenty low-resource languages."
        }
    }
    parsed = parse_doaj_article(sample_item)
    assert "Transformer Models" in parsed["title"]
    assert parsed["year"] == 2023
    assert parsed["is_doaj_indexed"] is True
    assert parsed["doi"] == "10.5555/jmlr.2023.01"
    assert parsed["source"] == "doaj"

def test_parse_hal_doc():
    from backend.app.metadata.hal import parse_hal_doc
    sample_doc = {
        "title_s": ["Decentralized Federated Learning over Heterogeneous Networks"],
        "authFullName_s": ["Jean Dupont", "Claire Martin"],
        "producedDateY_i": 2022,
        "journalTitle_s": "IEEE Transactions on Signal Processing",
        "doiId_s": "10.1109/TSP.2022.001",
        "uri_s": "https://hal.science/hal-03456789",
        "abstract_s": ["We analyze convergence guarantees for non-IID federated training."]
    }
    parsed = parse_hal_doc(sample_doc)
    assert "Decentralized Federated Learning" in parsed["title"]
    assert parsed["year"] == 2022
    assert len(parsed["authors"]) == 2
    assert parsed["doi"] == "10.1109/tsp.2022.001"
    assert parsed["source"] == "hal"

def test_html_report_generation():
    from backend.app.services.report_generator import generate_html_report
    loaded = get_analysis_result("eb774d3c80ab6663")
    assert loaded is not None
    res = AnalysisResult.model_validate(loaded)
    html = generate_html_report(res)
    assert "<!DOCTYPE html>" in html
    assert "VERITAS Citation Verifier" in html
    assert "Integrity Score" in html
    assert "Audit Trail & Bibliographic Verification" in html

def test_mla_and_chicago_formatters():
    from backend.app.services.citation_suggester import format_mla, format_chicago
    authors = ["Ashish Vaswani", "Noam Shazeer"]
    title = "Attention is all you need"
    venue = "Advances in Neural Information Processing Systems"
    year = 2017
    doi = "10.5555/3295222.3295349"

    mla = format_mla(authors, title, venue, year, doi)
    assert "Vaswani, Ashish, and Noam Shazeer." in mla
    assert '"Attention is all you need."' in mla

    chicago = format_chicago(authors, title, venue, year, doi)
    assert "Vaswani, Ashish" in chicago
    assert "2017." in chicago

