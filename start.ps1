# Citation Verifier Startup Script (PowerShell)
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting Citation Verifier Application" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

$Root = $PSScriptRoot

Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8001 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root'; .\venv\Scripts\uvicorn.exe backend.app.main:app --host 127.0.0.1 --port 8001 --reload"

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting Vite Frontend on http://127.0.0.1:5180 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root\frontend'; npm run dev"

Write-Host "`nBoth services launched!" -ForegroundColor Green
Write-Host "Frontend Web UI:  http://127.0.0.1:5180" -ForegroundColor White
Write-Host "Backend API Docs: http://127.0.0.1:8001/docs" -ForegroundColor White
