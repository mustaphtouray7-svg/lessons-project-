# Simple production runner using waitress
# Usage: powershell -ExecutionPolicy Bypass -File run_prod.ps1

$env:LESSONS_SECRET = $env:LESSONS_SECRET
if (-not $env:LESSONS_SECRET) {
    Write-Host "WARNING: LESSONS_SECRET is not set; set it before production use." -ForegroundColor Yellow
}

# Run waitress on port 8000
Write-Host "Starting waitress on port 8000..."
waitress-serve --port=8000 app:app
