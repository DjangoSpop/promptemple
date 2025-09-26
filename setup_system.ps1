# PromptCraft Template System Setup Script for Windows
# This script sets up the complete template management system

Write-Host "🚀 PromptCraft Template System Setup" -ForegroundColor Green
Write-Host "=" * 50

# Check if we're in the right directory
if (-not (Test-Path "manage.py")) {
    Write-Host "❌ Error: manage.py not found. Please run this script from the Django project root." -ForegroundColor Red
    exit 1
}

# Function to run commands and check results
function Run-Command {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "🔄 $Description..." -ForegroundColor Yellow
    
    try {
        $result = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $Description completed successfully" -ForegroundColor Green
            if ($result) {
                Write-Host "   Output: $result" -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Host "❌ $Description failed" -ForegroundColor Red
            Write-Host "   Error: $result" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ $Description failed with exception: $_" -ForegroundColor Red
        return $false
    }
}

# Check Python installation
Write-Host "🔍 Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Install requirements if requirements.txt exists
if (Test-Path "requirements.txt") {
    if (-not (Run-Command "pip install -r requirements.txt" "Installing Python dependencies")) {
        Write-Host "❌ Failed to install dependencies. Please check requirements.txt" -ForegroundColor Red
        exit 1
    }
}

# Create migrations and migrate
$setupSteps = @(
    @("python manage.py makemigrations", "Creating database migrations"),
    @("python manage.py makemigrations templates", "Creating template migrations"),
    @("python manage.py migrate", "Applying database migrations")
)

foreach ($step in $setupSteps) {
    if (-not (Run-Command $step[0] $step[1])) {
        Write-Host "❌ Setup failed. Please check the errors above." -ForegroundColor Red
        exit 1
    }
}

# Run the Python setup script to create sample data
if (-not (Run-Command "python setup_system.py" "Setting up sample data and checking system")) {
    Write-Host "❌ Failed to set up sample data." -ForegroundColor Red
    exit 1
}

# Test the ingestion system
Write-Host "🧪 Testing ingestion system..." -ForegroundColor Cyan
if (Test-Path "test_ingestion.py") {
    Run-Command "python test_ingestion.py" "Running ingestion test"
}

Write-Host ""
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "=" * 50
Write-Host "🚀 Quick Start Commands:" -ForegroundColor Cyan
Write-Host "   Start server:    python manage.py runserver" -ForegroundColor White
Write-Host "   Admin panel:     http://localhost:8000/admin/" -ForegroundColor White
Write-Host "   API endpoints:   http://localhost:8000/api/templates/" -ForegroundColor White
Write-Host ""
Write-Host "🔑 Admin Credentials:" -ForegroundColor Cyan
Write-Host "   Username: admin" -ForegroundColor White
Write-Host "   Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "📝 Test Ingestion:" -ForegroundColor Cyan
Write-Host "   python test_ingestion.py" -ForegroundColor White
Write-Host "   python manage.py ingest_prompts --source PROMPT_GOLDMINE_100K.md --type md" -ForegroundColor White
Write-Host ""
Write-Host "📖 Documentation: TEMPLATE_SYSTEM_DOCS.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔧 Advanced Commands:" -ForegroundColor Cyan
Write-Host "   Bulk upload:     /admin/templates/template/bulk-upload/" -ForegroundColor White
Write-Host "   Analytics:       /admin/templates/template/analytics/" -ForegroundColor White
Write-Host "   API suggestions: /api/templates/suggestions/" -ForegroundColor White

# Offer to start the server
Write-Host ""
$startServer = Read-Host "Would you like to start the development server now? (y/N)"
if ($startServer -eq "y" -or $startServer -eq "Y") {
    Write-Host "🌐 Starting development server..." -ForegroundColor Green
    python manage.py runserver
}