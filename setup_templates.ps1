# Setup Templates PowerShell Script
# This script helps set up the template database by running population and verification scripts.

Write-Host "Template Setup for Windows" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python and try again."
    exit 1
}

# Check and install dependencies
Write-Host "Checking and installing dependencies..." -ForegroundColor Cyan
python -m pip install django requests tabulate

# Ensure migrations are applied
Write-Host "Applying any pending database migrations..." -ForegroundColor Cyan
python manage.py migrate

# Run the population script
Write-Host "Populating templates..." -ForegroundColor Cyan
python populate_templates.py

# Ask to run verification
$verification = Read-Host "Run verification script? (y/n)"
if ($verification -eq "y") {
    # Run the verification script
    Write-Host "Running verification..." -ForegroundColor Cyan
    python verify_templates.py
}

Write-Host "Setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the development server, run: python manage.py runserver" -ForegroundColor Yellow

# Ask if user wants to start the server
$startServer = Read-Host "Start development server now? (y/n)"
if ($startServer -eq "y") {
    Write-Host "Starting development server..." -ForegroundColor Cyan
    Write-Host "Visit http://localhost:8000/api/templates/ to see the templates API." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop the server when done." -ForegroundColor Yellow
    Write-Host ""
    python manage.py runserver
}
