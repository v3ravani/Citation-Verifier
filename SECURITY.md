# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within Citation Verifier, please report it privately by emailing `ravaniviraj@gmail.com`. Please include a detailed description of the vulnerability, steps to reproduce, and any relevant proof-of-concept material.

Reports are acknowledged within 48 hours.

## Security Architecture

Citation Verifier incorporates defense-in-depth engineering practices:

### 1. Document Extraction & Execution Safety
- Uploaded files are strictly validated for MIME type and file signature.
- Only machine-readable PDF formats are processed.
- No content extracted from uploaded PDFs is executed or passed to shell evaluators.
- PyMuPDF handles document rendering in sandboxed memory structures.

### 2. Path Traversal & Filesystem Hardening
- Paper identifiers are derived from cryptographic SHA-256 digests.
- File system inputs and identifiers undergo strict regex character filtering (`^[a-zA-Z0-9_\-]+$`) before any disk access.
- File writes are restricted to configured storage directories (`uploads/`, `data/`, `cache/`, `results/`, `logs/`).

### 3. API Resilience & Privacy Boundaries
- Outbound requests to Crossref and Semantic Scholar enforce strict timeouts (12 seconds) and rate-limit handling.
- Full PDF contents are never transmitted across the network; only extracted bibliographic queries (titles, DOIs, and author tokens) leave the host machine for verification.
- Local NLP embeddings and FAISS similarity indexing run completely on the host system without invoking external cloud generative AI services.
