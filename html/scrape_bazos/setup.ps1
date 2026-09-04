# PowerShell setup script for bazos scraper project
# Run this script in your project directory

Write-Host "Setting up Bazos Scraper Project..." -ForegroundColor Green

# Check if files already exist
$files = @("pyproject.toml", "scraper.py", "cli.py", "reporter.py", "example.py", "README.md")

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "✓ $file already exists" -ForegroundColor Yellow
    } else {
        Write-Host "✗ $file is missing" -ForegroundColor Red
    }
}

# Initialize uv project
Write-Host "`nInitializing uv environment..." -ForegroundColor Cyan
uv sync

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "`nYou can now run:" -ForegroundColor Cyan
Write-Host "  python cli.py --topic pc --keyword 'nas'" -ForegroundColor White
Write-Host "  python example.py" -ForegroundColor White
