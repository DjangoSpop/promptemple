# Production Setup Script for Windows
# This script sets up and runs the PromptCraft API in production mode

Write-Host "🚀 PromptCraft Production Setup" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

# Set environment variables for production
$env:DJANGO_SETTINGS_MODULE = "promptcraft.settings.production"
$env:DEBUG = "False"
$env:SECRET_KEY = "your-production-secret-key-change-this"

# PostgreSQL connection settings (update these for your Ubuntu PostgreSQL)
$env:DB_NAME = "promptcraft_db"
$env:DB_USER = "promptcraft_user"
$env:DB_PASSWORD = "fuckthat"
$env:DB_HOST = "localhost"  # or your Ubuntu IP if different
$env:DB_PORT = "5432"

Write-Host "Environment variables set:" -ForegroundColor Cyan
Write-Host "- DJANGO_SETTINGS_MODULE: $env:DJANGO_SETTINGS_MODULE"
Write-Host "- DEBUG: $env:DEBUG"
Write-Host "- Database: PostgreSQL on $env:DB_HOST:$env:DB_PORT"

# Install production dependencies
Write-Host "`nInstalling production dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install psycopg2-binary whitenoise dj-database-url

# Check database connection
Write-Host "`nChecking database connection..." -ForegroundColor Cyan
python check_db.py

# Apply migrations
Write-Host "`nApplying database migrations..." -ForegroundColor Cyan
python manage.py migrate

# Collect static files
Write-Host "`nCollecting static files..." -ForegroundColor Cyan
python manage.py collectstatic --noinput

# Create superuser if needed
$createSuperuser = Read-Host "Create superuser account? (y/n)"
if ($createSuperuser -eq "y") {
    Write-Host "Creating superuser..." -ForegroundColor Cyan
    python manage.py createsuperuser
}

# Populate templates
$populateTemplates = Read-Host "Populate template database? (y/n)"
if ($populateTemplates -eq "y") {
    Write-Host "Populating templates..." -ForegroundColor Cyan
    python template_db_tool.py populate
}

# Start the production server
Write-Host "`n🚀 Starting production server..." -ForegroundColor Green
Write-Host "API will be available at:" -ForegroundColor Yellow
Write-Host "- Main API: http://localhost:8000/api/" -ForegroundColor Yellow
Write-Host "- Admin: http://localhost:8000/admin/" -ForegroundColor Yellow
Write-Host "- API Docs: http://localhost:8000/api/schema/swagger-ui/" -ForegroundColor Yellow
Write-Host "- Health Check: http://localhost:8000/health/" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red

python manage.py runserver 0.0.0.0:8000