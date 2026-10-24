@echo off
echo ===================================================
echo Starting Citation Verifier Application
echo ===================================================

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8001 ...
start "Citation Verifier - Backend" cmd /k ".\venv\Scripts\uvicorn.exe backend.app.main:app --host 127.0.0.1 --port 8001 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Vite Frontend on http://127.0.0.1:5180 ...
start "Citation Verifier - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo Both services are running:
echo - Frontend Web UI:  http://127.0.0.1:5180
echo - Backend API Docs: http://127.0.0.1:8001/docs
echo ===================================================
