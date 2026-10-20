import io
import pytest
from fastapi.testclient import TestClient
import fitz
from backend.app.main import app

client = TestClient(app)

def create_sample_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()

def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["app"] == "Citation Verifier"

def test_upload_empty_file_rejected():
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    resp = client.post("/api/upload", files=files)
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()

def test_upload_non_pdf_rejected():
    files = {"file": ("paper.txt", b"Some text content", "text/plain")}
    resp = client.post("/api/upload", files=files)
    assert resp.status_code == 400
    assert "only machine-readable pdf" in resp.json()["detail"].lower()

def test_upload_valid_pdf():
    pdf_bytes = create_sample_pdf("Sample academic paper with machine readable text.")
    files = {"file": ("valid_paper.pdf", pdf_bytes, "application/pdf")}
    resp = client.post("/api/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "paper_id" in data
    assert data["pages"] == 1
    assert data["status"] == "uploaded"

def test_result_not_found():
    resp = client.get("/api/result/nonexistent12345")
    assert resp.status_code == 404

def test_cache_status():
    resp = client.get("/api/cache/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert "total_cached_queries" in data

def test_annotated_pdf_not_found():
    resp = client.get("/api/report/nonexistent9999/annotated-pdf")
    assert resp.status_code == 404

def test_suggest_citations_validation_error():
    # Too short (< 15 characters)
    resp = client.post("/api/suggest-citations", json={"text": "short"})
    assert resp.status_code == 422

def test_annotated_pdf_export_for_verified_paper():
    # eb774d3c80ab6663 exists in results
    resp = client.get("/api/report/eb774d3c80ab6663/annotated-pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert len(resp.content) > 1000

