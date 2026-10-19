# Contributing to Citation Verifier

Thank you for your interest in contributing to Citation Verifier. This project is dedicated to academic research integrity and reproducible software development.

## Mandatory Engineering Principles

Before contributing code, please ensure adherence to our core principles:

1. **No Fake Data**: Never invent dummy citation records, simulated similarity metrics, or hardcoded mock fixtures in production code.
2. **Local NLP Only**: All semantic embeddings and vector searches must run locally using Sentence-BERT and FAISS. Do not introduce dependencies on external generative AI APIs (OpenAI, Gemini, Claude, etc.).
3. **No Database**: Persistence must use the local filesystem (`uploads/`, `data/`, `cache/`, `results/`, `logs/`).
4. **Academic Design Standards**: The frontend follows a strict white-background academic research aesthetic. Do not add dark mode, neon accents, or generic SaaS templates.

## Development Setup

### Backend Setup
1. Create and activate a Python 3.11 virtual environment:
   ```bash
   py -3.11 -m venv venv
   .\venv\Scripts\activate  # Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run unit and integration tests:
   ```bash
   python -m pytest backend/tests -v
   ```
4. Start development server:
   ```bash
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```
2. Verify production build:
   ```bash
   npm run build
   ```
3. Start Vite dev server:
   ```bash
   npm run dev
   ```

## Pull Request Guidelines

- Ensure all 28 pytest unit and integration tests pass cleanly.
- Verify that `npm run build` succeeds with zero errors.
- Preserve type hints and docstrings across Python modules.
- Include concise commit messages explaining the architectural rationale for your changes.
