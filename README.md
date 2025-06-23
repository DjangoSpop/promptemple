# PromptCraft Backend

PromptCraft is a modular, scalable platform for AI prompt management, generation, and optimization. This repository contains the Django backend for the PromptCraft application.

## Project Structure

```
my_prmpt_bakend/
├── apps/                        # Django applications
│   ├── ai_services/             # AI service integrations
│   ├── analytics/               # Analytics and metrics
│   ├── core/                    # Core functionality
│   ├── gamification/            # User achievements and challenges
│   ├── templates/               # Prompt templates
│   └── users/                   # User management
├── promptcraft/                 # Django project settings
│   ├── settings/
│   │   ├── __init__.py          # Environment-based settings loader
│   │   ├── base.py              # Base settings
│   │   ├── development.py       # Development settings
│   │   ├── production.py        # Production settings
│   │   └── testing.py           # Testing settings
├── Dockerfile                   # Docker configuration
├── create_dir.ps1               # PowerShell script for creating app structure
├── setup.ps1                    # PowerShell setup script
└── requirements.txt             # Python dependencies
```

## Features

- Multi-provider AI service integrations (OpenAI, Anthropic, etc.)
- Advanced prompt management and template system
- User management with authentication and permissions
- Gamification with achievements, challenges, and rewards
- Analytics and insights for prompt usage and effectiveness
- Modular Django structure for easy extensibility

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL (for production) or SQLite (for development)
- Redis (for Celery tasks and caching)
- Docker (optional, for containerized setup)

### Windows-Specific Setup

1. Fix requirements file if needed:

```powershell
# This script will ensure requirements.txt exists and update Dockerfile references
.\fix_requirements.ps1
```

2. PowerShell Script Execution Policy:
   
If you receive a security error when trying to run the PowerShell scripts, you may need to allow script execution:

```powershell
# Run PowerShell as Administrator and execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or run scripts directly with:
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -Setup
```

### Using PowerShell Setup Script

The easiest way to set up the project is using the included PowerShell script:

```powershell
# Set up development environment
.\setup.ps1 -Setup

# Initialize database with sample data and admin user
.\setup.ps1 -InitializeDb -SampleData -CreateAdmin

# Run the development server
.\setup.ps1 -Run
```

### Manual Setup

1. Create a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create `.env` file from `.env.sample`:

```powershell
Copy-Item .env.sample .env
```

4. Run migrations:

```powershell
python manage.py migrate
```

5. Load fixtures:

```powershell
python manage.py loaddata apps/core/fixtures/ai_providers.json
python manage.py loaddata apps/core/fixtures/ai_models.json
python manage.py loaddata apps/core/fixtures/template_categories.json
```

6. Create a superuser:

```powershell
python manage.py createsuperuser
```

7. Run the development server:

```powershell
python manage.py runserver
```

## Docker Setup

### Using Docker Compose

The project includes a complete Docker Compose setup that launches the following services:
- PostgreSQL database
- Redis for caching and Celery
- Django backend web server
- Celery worker for background tasks
- Celery Beat for scheduled tasks
- Flutter web frontend with Nginx

To run the project using Docker:

```powershell
# Make sure you have a .env file with necessary environment variables
if (-not (Test-Path .env)) {
    Copy-Item .env.sample .env
    Write-Host "Created .env file from .env.sample - please update with your settings!" -ForegroundColor Yellow
}

# Start all services
docker-compose up -d

# Initialize database with one command
docker-compose exec web python manage.py initialize_project --admin --sample-data

# Or run individual commands:
# Create an admin user
docker-compose exec web python manage.py createsuperuser

# Load fixtures
docker-compose exec web python manage.py loaddata apps/core/fixtures/ai_providers.json
docker-compose exec web python manage.py loaddata apps/core/fixtures/ai_models.json
docker-compose exec web python manage.py loaddata apps/core/fixtures/template_categories.json
```

### Accessing Services

- **Django Backend**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/docs/
- **Flutter Web Frontend**: http://localhost:3000

### Docker Compose Commands

```powershell
# Start services in the background
docker-compose up -d

# View logs from all services
docker-compose logs -f

# View logs from a specific service
docker-compose logs -f web

# Stop services
docker-compose down

# Rebuild containers (after code changes)
docker-compose build

# Rebuild and restart services
docker-compose up -d --build
```

## Creating a New Django App

You can easily create a new Django app with the proper structure using the provided PowerShell script:

```powershell
.\create_dir.ps1 your_app_name
```

This will create a new app with the following structure:

```
apps/your_app_name/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── views.py
├── urls.py
├── serializers.py
├── services.py
├── fixtures/
├── templates/
│   └── your_app_name/
├── static/
│   └── your_app_name/
│       ├── css/
│       └── js/
├── migrations/
│   └── __init__.py
├── management/
│   ├── __init__.py
│   └── commands/
│       └── __init__.py
├── templatetags/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    └── test_views.py
```

## API Documentation

API documentation is available at `/api/docs/` when the server is running.

## Project Management Commands

The project includes several management commands:

- `initialize_project`: Set up the project with initial data
- `create_sample_data`: Create sample data for development

Example usage:

```powershell
python manage.py initialize_project --admin --sample-data
python manage.py create_sample_data
```

## Running Tests

```powershell
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.your_app_name
```
