import re
from pathlib import Path
from typing import List, Tuple, Dict, Any
import fitz  # PyMuPDF
from backend.app.core.logging_config import logger

class PDFExtractionError(Exception):
    pass

class ScannedPDFError(PDFExtractionError):
    pass

def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extracts text and page-level information from a PDF file using PyMuPDF.
    
    Returns:
        (full_text, pages_data)
        where pages_data is a list of dicts: [{"page_number": int, "text": str}]
    """
    if not pdf_path.exists():
        raise PDFExtractionError(f"File not found: {pdf_path}")
    
    if pdf_path.stat().st_size == 0:
        raise PDFExtractionError("PDF file is empty (0 bytes).")
        
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path.name}: {e}")
        raise PDFExtractionError(f"Corrupt or invalid PDF file: {e}")
        
    if len(doc) == 0:
        doc.close()
        raise PDFExtractionError("PDF contains 0 pages.")
        
    pages_data = []
    total_chars = 0
    full_text_parts = []
    
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        raw_text = page.get_text("text") or ""
        # Basic cleanup: remove null bytes and normalize line endings
        cleaned_text = raw_text.replace("\x00", "")
        # De-hyphenate broken words across line breaks (e.g. "experi-\nment" -> "experiment")
        dehyphenated = re.sub(r'(\w+)-\n(\w+)', r'\1\2', cleaned_text)
        
        pages_data.append({
            "page_number": page_idx + 1,
            "text": dehyphenated,
            "raw_text": raw_text
        })
        total_chars += len(dehyphenated.strip())
        full_text_parts.append(dehyphenated)
        
    doc.close()
    
    # Check if scanned/image-only
    # Average chars per page threshold
    if total_chars < 80:
        raise ScannedPDFError(
            "No machine-readable text detected. This document appears to be a scanned or image-only PDF."
        )
        
    full_text = "\n\n".join(full_text_parts)
    return full_text, pages_data

def guess_paper_title(full_text: str, pages_data: List[Dict[str, Any]]) -> str:
    """
    Attempts to heuristic guess the paper title from the first page text.
    """
    if not pages_data:
        return "Untitled Document"
        
    first_page = pages_data[0]["text"].strip()
    lines = [l.strip() for l in first_page.split("\n") if l.strip()]
    
    # Typically the title is in the first 5 non-empty lines, longest or uppercase
    candidate_lines = []
    for line in lines[:8]:
        # Filter out common header phrases
        lower = line.lower()
        if any(h in lower for h in ["ieee", "arxiv", "proceedings", "conference", "journal", "volume", "issn", "doi"]):
            continue
        if len(line) > 15:
            candidate_lines.append(line)
            
    if candidate_lines:
        return candidate_lines[0]
    elif lines:
        return lines[0][:150]
        
    return "Untitled Document"
