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
# 🚀 PromptCraft Backend

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Supported-red.svg)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supported-blue.svg)](https://www.postgresql.org/)

> **Enterprise-Grade AI Prompt Engineering Platform** - A comprehensive Django backend powering the next generation of AI prompt management, optimization, and monetization.

## ✨ Overview

PromptCraft is a full-featured, production-ready backend system designed for AI prompt engineering and management. Built with Django and modern web technologies, it provides a complete platform for creating, optimizing, and monetizing AI prompts through an intuitive API-first architecture.

### 🎯 Key Highlights

- **🤖 Advanced AI Integration**: DeepSeek, OpenAI, Anthropic with intelligent fallback
- **📊 Real-time Analytics**: Comprehensive user behavior tracking and conversion analytics
- **💰 Monetization Ready**: Subscription management, usage quotas, and payment processing
- **🎮 Gamification Engine**: Achievements, challenges, and user engagement features
- **⚡ High Performance**: Redis caching, async processing, and optimized queries
- **🔒 Enterprise Security**: JWT authentication, rate limiting, and audit trails
- **📱 API-First Design**: RESTful APIs with OpenAPI documentation
- **🐳 Container Ready**: Docker and Docker Compose support for easy deployment

## 🌟 Core Features

### 🤖 AI & Machine Learning
- **RAG Agent**: Retrieval-Augmented Generation for context-aware prompt optimization
- **Multi-Provider Support**: DeepSeek, OpenAI, Anthropic with automatic failover
- **Prompt Optimization**: AI-powered prompt enhancement and refinement
- **Template Intelligence**: Smart template suggestions and auto-completion
- **Usage Analytics**: Token tracking, cost optimization, and performance metrics

### 📝 Template Management System
- **Dynamic Templates**: Flexible field-based template creation and management
- **Category Organization**: Hierarchical template categorization and search
- **Usage Tracking**: Template performance analytics and popularity metrics
- **Version Control**: Template versioning and change history
- **Bulk Operations**: Mass import/export and template synchronization

### 💳 Billing & Monetization
- **Subscription Plans**: Flexible tiered pricing with feature gates
- **Usage Quotas**: Daily/monthly limits with automatic enforcement
- **Payment Processing**: Stripe integration with webhook handling
- **Invoice Generation**: Automated billing and receipt management
- **Coupon System**: Discount codes and promotional campaigns

### 🎮 Gamification & Engagement
- **Achievement System**: Unlockable badges and milestones
- **Daily Challenges**: Time-limited tasks and rewards
- **User Levels**: Experience points and progression tracking
- **Credit Economy**: Virtual currency system for premium features
- **Leaderboards**: Competitive rankings and social features

### 📊 Analytics & Insights
- **User Behavior Tracking**: Comprehensive event logging and analysis
- **Conversion Funnels**: Multi-step user journey analytics
- **A/B Testing**: Experiment management and statistical analysis
- **Performance Metrics**: System health, API usage, and error tracking
- **Custom Dashboards**: Real-time monitoring and reporting

### 💬 Real-time Communication
- **WebSocket Chat**: Real-time messaging with Django Channels
- **SSE Streaming**: Server-Sent Events for live updates
- **Chat Sessions**: Persistent conversation history and management
- **Template Extraction**: Automatic prompt template discovery
- **Message Archiving**: Long-term storage and search capabilities

### 🔐 Security & Authentication
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: Granular permissions and access control
- **Rate Limiting**: API throttling and abuse prevention
- **Audit Logging**: Comprehensive security event tracking
- **Data Encryption**: Sensitive data protection and compliance

## 🏗️ Architecture

```
PromptCraft Backend
├── 🎯 API Layer (Django REST Framework)
├── 🔄 Async Processing (Celery + Redis)
├── 💾 Data Layer (PostgreSQL + Redis Cache)
├── 🤖 AI Services (DeepSeek, OpenAI, Anthropic)
├── 💬 Real-time (Django Channels + WebSockets)
├── 📊 Analytics (Custom Events + Metrics)
├── 💰 Billing (Stripe Integration)
└── 🎮 Gamification (Achievements + Challenges)
```

### Tech Stack

**Backend Framework:**
- Django 4.2+ with Django REST Framework
- Django Channels for WebSocket support
- Celery for background task processing

**Database & Caching:**
- PostgreSQL for primary data storage
- Redis for caching, sessions, and message queuing
- SQLite for development and testing

**AI & ML:**
- DeepSeek API integration
- OpenAI GPT integration
- Anthropic Claude integration
- LangChain for RAG implementation

**Infrastructure:**
- Docker & Docker Compose
- Nginx for production serving
- Gunicorn for WSGI serving
- Daphne for ASGI/WebSocket serving

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **PostgreSQL** (production) or **SQLite** (development)
- **Redis** (recommended for full functionality)
- **Docker** (optional, for containerized setup)

### Windows Setup (Recommended)

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/yourusername/promptcraft-backend.git
   cd promptcraft-backend
   ```

2. **Run the automated setup:**
   ```powershell
   # Set up development environment
   .\setup.ps1 -Setup

   # Initialize database with sample data
   .\setup.ps1 -InitializeDb -SampleData -CreateAdmin

   # Start the development server
   .\setup.ps1 -Run
   ```

3. **Access the application:**
   - **API**: http://localhost:8000/api/
   - **Admin Panel**: http://localhost:8000/admin/
   - **API Documentation**: http://localhost:8000/api/docs/

### Manual Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Database setup:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Load sample data:**
   ```bash
   python manage.py loaddata apps/core/fixtures/*
   python manage.py populate_templates
   ```

6. **Start development server:**
   ```bash
   python manage.py runserver
   ```

## 🐳 Docker Deployment

### Development with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run management commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/promptcraft
# Or for SQLite (development):
# DATABASE_URL=sqlite:///db.sqlite3

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# AI Service Configuration
DEEPSEEK_API_KEY=your-deepseek-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Stripe Configuration (for billing)
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Sentry (Error Monitoring)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Security
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 📚 API Documentation

### Core Endpoints

#### 🤖 AI Services
```
POST   /api/ai/optimize/          # Optimize prompts with RAG
POST   /api/ai/retrieve/          # Retrieve relevant documents
POST   /api/ai/answer/            # Generate answers with context
GET    /api/ai/stats/             # AI service statistics
```

#### 📝 Templates
```
GET    /api/templates/            # List templates (with pagination)
POST   /api/templates/            # Create new template
GET    /api/templates/{id}/       # Get template details
PUT    /api/templates/{id}/       # Update template
DELETE /api/templates/{id}/       # Delete template
GET    /api/templates/categories/ # List categories
```

#### 💳 Billing
```
GET    /api/billing/plans/        # List subscription plans
POST   /api/billing/subscribe/    # Create subscription
GET    /api/billing/usage/        # Get usage statistics
POST   /api/billing/webhook/      # Stripe webhook handler
```

#### 🎮 Gamification
```
GET    /api/gamification/achievements/    # User achievements
GET    /api/gamification/challenges/     # Daily challenges
GET    /api/gamification/leaderboard/    # Leaderboard rankings
POST   /api/gamification/claim-reward/   # Claim challenge rewards
```

#### 📊 Analytics
```
GET    /api/analytics/dashboard/         # Analytics dashboard
GET    /api/analytics/events/            # User events
POST   /api/analytics/track/             # Track custom events
GET    /api/analytics/funnels/           # Conversion funnels
```

#### 💬 Chat & Real-time
```
WebSocket: ws://localhost:8000/ws/chat/{session_id}/
SSE:       GET /api/chat/stream/{session_id}/
POST       /api/chat/sessions/           # Create chat session
GET        /api/chat/messages/           # Get messages
```

### Authentication

All API endpoints require authentication using JWT tokens:

```bash
# Obtain access token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token in requests
curl -H "Authorization: Bearer <your-token>" \
  http://localhost:8000/api/templates/
```

## 🎯 Usage Examples

### 🤖 Prompt Optimization

```python
import requests

# Optimize a prompt using RAG
response = requests.post('http://localhost:8000/api/ai/optimize/', 
    headers={'Authorization': 'Bearer <token>'},
    json={
        'session_id': 'unique-session-123',
        'original': 'Write a marketing email for a new product launch',
        'mode': 'deep',
        'context': {
            'intent': 'marketing',
            'domain': 'e-commerce'
        },
        'budget': {
            'tokens_in': 2000,
            'tokens_out': 800,
            'max_credits': 5
        }
    })

optimized_prompt = response.json()['optimized']
citations = response.json()['citations']
```

### 📝 Template Management

```python
# Create a new template
template_data = {
    'title': 'Product Launch Email',
    'category': 'marketing',
    'description': 'Template for product launch announcements',
    'fields': [
        {'name': 'product_name', 'type': 'text', 'required': True},
        {'name': 'target_audience', 'type': 'select', 'options': ['B2B', 'B2C']}
    ],
    'content': 'Introducing {{product_name}} - the perfect solution for {{target_audience}}...'
}

response = requests.post('http://localhost:8000/api/templates/',
    headers={'Authorization': 'Bearer <token>'},
    json=template_data)
```

### 💬 Real-time Chat

```javascript
// WebSocket connection for real-time chat
const ws = new WebSocket('ws://localhost:8000/ws/chat/session-123/');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data.message);
};

// Send a message
ws.send(JSON.stringify({
    type: 'chat_message',
    message: 'Hello, can you help me optimize this prompt?',
    user_id: 123
}));
```

## 🔧 Development

### Project Structure

```
promptcraft-backend/
├── apps/                          # Django applications
│   ├── ai_services/              # AI integrations & RAG
│   ├── analytics/                # Analytics & tracking
│   ├── billing/                  # Subscription & payments
│   ├── chat/                     # Real-time chat system
│   ├── core/                     # Core functionality
│   ├── gamification/             # Achievements & challenges
│   ├── orchestrator/             # Workflow management
│   ├── templates/                # Template management
│   └── users/                    # User management
├── promptcraft/                  # Django project settings
│   ├── settings/
│   │   ├── base.py              # Base configuration
│   │   ├── development.py       # Development settings
│   │   ├── production.py        # Production settings
│   │   └── testing.py           # Test configuration
├── static/                       # Static files
├── media/                        # User uploads
├── templates/                    # Django templates
├── Dockerfile                    # Docker configuration
├── docker-compose.yml            # Development services
├── requirements.txt              # Python dependencies
├── manage.py                     # Django management script
└── setup.ps1                     # Windows setup script
```

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.ai_services

# Run with coverage
coverage run manage.py test
coverage report
```

### Code Quality

```bash
# Run linting
flake8 .

# Format code
black .

# Type checking
mypy .
```

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in production settings
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up SSL/TLS certificates
- [ ] Configure database backups
- [ ] Set up monitoring and logging
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up process manager (systemd/supervisor)
- [ ] Configure environment variables
- [ ] Set up CDN for static files
- [ ] Configure firewall and security groups

### Production Deployment Options

#### 1. Docker + Nginx + Gunicorn

```nginx
# nginx.conf
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

#### 2. Cloud Platforms

**Heroku:**
```bash
heroku create your-app-name
heroku config:set DEBUG=False
git push heroku main
```

**Railway:**
```bash
railway login
railway init
railway up
```

**AWS/DigitalOcean:**
Use the provided Docker Compose configuration for easy cloud deployment.

### Monitoring & Maintenance

#### Health Checks
```
GET /api/health/          # System health status
GET /api/health/database/ # Database connectivity
GET /api/health/redis/    # Redis connectivity
GET /api/health/ai/       # AI service status
```

#### Logs
```bash
# View application logs
docker-compose logs -f web

# View Celery logs
docker-compose logs -f celery

# System monitoring
python manage.py shell -c "from apps.core.health_checks import *"
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run the test suite: `python manage.py test`
5. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](http://localhost:8000/api/docs/) (when running)
- [Frontend Integration Guide](FRONTEND_INTEGRATION_GUIDE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Template System Docs](TEMPLATE_SYSTEM_DOCS.md)

### Community
- **Issues**: [GitHub Issues](https://github.com/yourusername/promptcraft-backend/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/promptcraft-backend/discussions)
- **Discord**: Join our [Discord Server](https://discord.gg/promptcraft)

### Professional Support
For enterprise support, custom development, or consulting services:
- Email: support@promptcraft.dev
- Website: https://promptcraft.dev

## 🙏 Acknowledgments

- **Django Community** for the excellent web framework
- **DeepSeek, OpenAI, Anthropic** for AI API access
- **Stripe** for payment processing
- **Redis** for high-performance caching
- **PostgreSQL** for robust data storage

---

<div align="center">

**Built with ❤️ for the AI prompt engineering community**

⭐ Star us on GitHub | 📖 Read the docs | 🚀 Get started today

[🌐 Website](https://promptcraft.dev) • [📧 Contact](mailto:hello@promptcraft.dev) • [🐛 Issues](https://github.com/yourusername/promptcraft-backend/issues)

</div>