import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.metadata.core_ac import parse_core_work
from backend.app.metadata.orcid import parse_orcid_work_result
from backend.app.metadata.clinicaltrials import parse_clinical_study, extract_nct_id
from backend.app.metadata.figshare import parse_figshare_article
from backend.app.metadata.osf import parse_osf_item
from backend.app.metadata.repec import parse_repec_html_item
from backend.app.metadata.nasa_ads import parse_ads_doc
from backend.app.metadata.ieee import parse_ieee_article
from backend.app.metadata.scopus import parse_scopus_entry
from backend.app.metadata.wos import parse_wos_doc
from backend.app.metadata.dimensions import parse_dimensions_publication
from backend.app.citations.reference_parser import extract_reference_title, parse_reference
from backend.app.services.result_manager import get_analysis_result

client = TestClient(app)

def test_parse_core_work():
    sample = {
        "title": "A Decentralized Federated Learning Architecture",
        "authors": [{"name": "Alice Johnson"}, {"name": "Bob Smith"}],
        "yearPublished": 2023,
        "doi": "10.1234/core.2023.001",
        "publisher": "CORE Open Repository",
        "abstract": "We introduce a novel peer-to-peer consensus model."
    }
    parsed = parse_core_work(sample)
    assert parsed["title"] == "A Decentralized Federated Learning Architecture"
    assert len(parsed["authors"]) == 2
    assert parsed["year"] == 2023
    assert parsed["doi"] == "10.1234/core.2023.001"
    assert parsed["source"] == "core"

def test_parse_orcid_work_result():
    sample = {
        "work-title": "Quantum Error Correction on NISQ Devices",
        "family-names": "Feynman",
        "given-names": "Richard",
        "publication-year": 2022,
        "external-ids": {
            "external-id": [
                {"external-id-type": "doi", "external-id-value": "10.1038/s41586-022-0001"}
            ]
        }
    }
    parsed = parse_orcid_work_result(sample)
    assert parsed is not None
    assert parsed["title"] == "Quantum Error Correction on NISQ Devices"
    assert "Richard Feynman" in parsed["authors"]
    assert parsed["doi"] == "10.1038/s41586-022-0001"
    assert parsed["source"] == "orcid"

def test_parse_clinical_study():
    sample = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT04280705",
                "briefTitle": "Adaptive COVID-19 Treatment Trial (ACTT-1)",
                "organization": {"fullName": "National Institute of Allergy and Infectious Diseases"}
            },
            "statusModule": {
                "startDateStruct": {"date": "February 21, 2020"}
            },
            "descriptionModule": {
                "briefSummary": "A multicenter trial to evaluate remdesivir."
            }
        }
    }
    parsed = parse_clinical_study(sample)
    assert parsed["title"] == "Adaptive COVID-19 Treatment Trial (ACTT-1)"
    assert parsed["year"] == 2020
    assert "NCT04280705" in parsed["venue"]
    assert parsed["source"] == "clinicaltrials"
    assert extract_nct_id("Study conducted under NCT04280705.") == "NCT04280705"

def test_parse_figshare_article():
    sample = {
        "title": "Benchmark Dataset for Multi-modal Sensor Fusion",
        "authors": [{"full_name": "Carol Danvers"}],
        "published_date": "2021-08-15T10:00:00Z",
        "doi": "10.6084/m9.figshare.1234567.v1"
    }
    parsed = parse_figshare_article(sample)
    assert parsed["title"] == "Benchmark Dataset for Multi-modal Sensor Fusion"
    assert parsed["authors"] == ["Carol Danvers"]
    assert parsed["year"] == 2021
    assert parsed["doi"] == "10.6084/m9.figshare.1234567.v1"
    assert parsed["source"] == "figshare"

def test_parse_osf_item():
    sample = {
        "attributes": {
            "title": "Reproducibility in Machine Learning: A Survey",
            "date_published": "2020-05-01",
            "doi": "10.31219/osf.io/abcde"
        }
    }
    parsed = parse_osf_item(sample)
    assert parsed is not None
    assert parsed["title"] == "Reproducibility in Machine Learning: A Survey"
    assert parsed["year"] == 2020
    assert parsed["doi"] == "10.31219/osf.io/abcde"
    assert parsed["source"] == "osf"

def test_parse_repec_html_item():
    parsed = parse_repec_html_item(
        "Monetary Policy Under Ambiguity",
        "Lars Peter Hansen, Thomas J. Sargent",
        "2018",
        "https://econpapers.repec.org/paper/example.htm"
    )
    assert parsed["title"] == "Monetary Policy Under Ambiguity"
    assert parsed["year"] == 2018
    assert parsed["source"] == "repec"

def test_parse_nasa_ads_doc():
    sample = {
        "title": ["Gravitational Wave Astrometry with Pulsar Timing Arrays"],
        "author": ["Mingarelli, Chiara M. F.", "Taylor, Stephen R."],
        "year": "2019",
        "doi": ["10.3847/1538-4357/ab237f"],
        "pub": "The Astrophysical Journal"
    }
    parsed = parse_ads_doc(sample)
    assert "Gravitational Wave Astrometry" in parsed["title"]
    assert parsed["year"] == 2019
    assert parsed["doi"] == "10.3847/1538-4357/ab237f"
    assert parsed["source"] == "nasa_ads"

def test_parse_ieee_article():
    sample = {
        "title": "A Survey on Deep Learning for Big Data",
        "authors": {"authors": [{"full_name": "Jane Doe"}]},
        "publication_year": 2021,
        "doi": "10.1109/JPROC.2021.001",
        "publication_title": "Proceedings of the IEEE"
    }
    parsed = parse_ieee_article(sample)
    assert parsed["title"] == "A Survey on Deep Learning for Big Data"
    assert parsed["year"] == 2021
    assert parsed["doi"] == "10.1109/jproc.2021.001"
    assert parsed["source"] == "ieee"

def test_parse_scopus_entry():
    sample = {
        "dc:title": "Reinforcement Learning in Robotics: A Survey",
        "dc:creator": "Kober, Jens",
        "prism:coverDate": "2013-10-01",
        "prism:doi": "10.1177/0278364913495721",
        "prism:publicationName": "The International Journal of Robotics Research",
        "citedby-count": "1500"
    }
    parsed = parse_scopus_entry(sample)
    assert parsed["title"] == "Reinforcement Learning in Robotics: A Survey"
    assert parsed["year"] == 2013
    assert parsed["doi"] == "10.1177/0278364913495721"
    assert parsed["citation_count"] == 1500
    assert parsed["source"] == "scopus"

def test_parse_wos_doc():
    sample = {
        "title": "Global Biodiversity Loss and Ecosystem Services",
        "names": {"authors": [{"wosStandard": "Cardinale, BJ"}]},
        "source": {"publishYear": 2012, "sourceTitle": "Nature"},
        "identifiers": {"doi": "10.1038/nature11148"},
        "citations": {"wos": 2500}
    }
    parsed = parse_wos_doc(sample)
    assert parsed["title"] == "Global Biodiversity Loss and Ecosystem Services"
    assert parsed["year"] == 2012
    assert parsed["doi"] == "10.1038/nature11148"
    assert parsed["source"] == "wos"

def test_parse_dimensions_publication():
    sample = {
        "title": "Graph Convolutional Networks for Semi-Supervised Classification",
        "authors": [{"first_name": "Thomas", "last_name": "Kipf"}],
        "year": 2017,
        "doi": "10.48550/arXiv.1609.02907",
        "journal": {"title": "ICLR"},
        "times_cited": 9000
    }
    parsed = parse_dimensions_publication(sample)
    assert "Graph Convolutional Networks" in parsed["title"]
    assert parsed["year"] == 2017
    assert parsed["citation_count"] == 9000
    assert parsed["source"] == "dimensions"

def test_enhanced_reference_title_extraction():
    # 1. Title starting with digits
    raw1 = "1. Chen, X., & Gupta, A. (2015). 3D convolutional networks for video representation. In CVPR (pp. 1-9)."
    assert extract_reference_title(raw1) is not None
    assert "3D convolutional networks" in extract_reference_title(raw1)

    # 2. Title with question mark
    raw2 = 'Vaswani, A. et al. (2017). "Attention is all you need?" Advances in Neural Information Processing Systems.'
    assert extract_reference_title(raw2) == "Attention is all you need?"

    # 3. Subtitle with colon
    raw3 = "Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). BERT: Pre-training of deep bidirectional transformers for language understanding. arXiv:1810.04805."
    extracted = extract_reference_title(raw3)
    assert extracted is not None
    assert "BERT: Pre-training" in extracted

def test_user_verification_api_lifecycle():
    # Uses sample paper ID eb774d3c80ab6663 present in test data
    paper_id = "eb774d3c80ab6663"
    result = get_analysis_result(paper_id)
    if not result:
        pytest.skip("Test paper not found in cache")

    # Mark reference #1 as verified by user
    verify_resp = client.post(
        f"/api/result/{paper_id}/reference/1/user-verify",
        json={"verified": True, "note": "Verified from physical university library print edition"}
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    ref1 = next(r for r in data["references"] if r["reference_id"] == 1)
    assert ref1["verification"]["is_user_verified"] is True
    assert ref1["verification"]["status"] == "user_verified"
    assert "Verified from physical university library" in ref1["verification"]["user_verification_note"]
    assert data["summary"]["user_verified"] >= 1

    # Now revert verification
    revert_resp = client.post(
        f"/api/result/{paper_id}/reference/1/user-verify",
        json={"verified": False}
    )
    assert revert_resp.status_code == 200
    revert_data = revert_resp.json()
    reverted_ref1 = next(r for r in revert_data["references"] if r["reference_id"] == 1)
    assert reverted_ref1["verification"]["is_user_verified"] is False
    assert reverted_ref1["verification"]["status"] != "user_verified"
