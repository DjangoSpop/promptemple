# 🎯 PromptCraft Django API Development Manual

## Table of Contents
1. [Project Setup & Environment](#1-project-setup--environment)
2. [Django Project Structure](#2-django-project-structure)
3. [Database Models Design](#3-database-models-design)
4. [Authentication System](#4-authentication-system)
5. [API Serializers](#5-api-serializers)
6. [ViewSets & Business Logic](#6-viewsets--business-logic)
7. [Gamification System](#7-gamification-system)
8. [AI Integration](#8-ai-integration)
9. [Analytics & Performance](#9-analytics--performance)
10. [Testing Strategy](#10-testing-strategy)
11. [Deployment & Production](#11-deployment--production)

---

## 1. Project Setup & Environment

### 🎯 Learning Objectives
- Understand Django project structure
- Set up virtual environments properly
- Configure settings for different environments
- Implement security best practices

### Step 1.1: Create Project Foundation

```bash
# Create project directory
mkdir promptcraft_backend
cd promptcraft_backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Create requirements.txt
touch requirements.txt
```

### Step 1.2: Install Dependencies

Add to `requirements.txt`:
```txt
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-filter==23.3
django-environ==0.11.2
celery==5.3.4
redis==5.0.1
psycopg2-binary==2.9.9
Pillow==10.1.0
gunicorn==21.2.0
whitenoise==6.6.0
dj-database-url==2.1.0
djangorestframework-simplejwt==5.3.0
django-extensions==3.2.3
openai==1.3.7
anthropic==0.7.7
requests==2.31.0
python-decouple==3.8
django-storages==1.14.2
boto3==1.34.0
django-cacheops==7.0.2
django-debug-toolbar==4.2.0
pytest-django==4.7.0
coverage==7.3.2
```

```bash
# Install dependencies
pip install -r requirements.txt
```

### Step 1.3: Create Django Project

```bash
# Create Django project
django-admin startproject promptcraft .

# Create apps directory structure
mkdir apps
touch apps/__init__.py

# Create individual apps
cd apps
python ../manage.py startapp users
python ../manage.py startapp templates
python ../manage.py startapp gamification
python ../manage.py startapp analytics
python ../manage.py startapp ai_services
python ../manage.py startapp core
```

### 💡 **Why This Structure?**
- **Modular Design**: Each app handles specific functionality
- **Scalability**: Easy to add new features
- **Maintainability**: Clear separation of concerns
- **Team Collaboration**: Multiple developers can work on different apps

---

## 2. Django Project Structure

### Step 2.1: Configure Settings Structure

Create `promptcraft/settings/` directory:
```bash
mkdir promptcraft/settings
touch promptcraft/settings/__init__.py
```

**promptcraft/settings/base.py** - Common settings:
```python
import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'django_extensions',
]

LOCAL_APPS = [
    'apps.users',
    'apps.templates',
    'apps.gamification',
    'apps.analytics',
    'apps.ai_services',
    'apps.core',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'promptcraft.urls'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

**promptcraft/settings/development.py** - Development settings:
```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CORS settings for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Debug toolbar
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

**promptcraft/settings/production.py** - Production settings:
```python
from .base import *

DEBUG = False
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', 
    default='yourdomain.com', 
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Production database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 💡 **Why Multiple Settings Files?**
- **Environment Isolation**: Different configs for dev/staging/production
- **Security**: Sensitive data only in production
- **Flexibility**: Easy to switch between environments
- **Team Work**: Developers can have custom local settings

---

## 3. Database Models Design

### 🎯 Learning Objectives
- Design normalized database schemas
- Implement model relationships
- Add validation and constraints
- Create efficient database indexes

### Step 3.1: User Model (apps/users/models.py)

```python

```

### 💡 **Key Model Design Principles:**

1. **UUID Primary Keys**: Better security than incremental IDs
2. **Validation**: Use Django validators for data integrity
3. **Help Text**: Document fields for future developers
4. **Indexes**: Add database indexes for frequently queried fields
5. **Properties**: Use Python properties for calculated fields
6. **Methods**: Add business logic methods to models

### Step 3.2: Template Models (apps/templates/models.py)

```python
from django.db import models
    
```

### 💡 **Advanced Model Features Explained:**

1. **Choices with TextChoices**: Type-safe enum values
2. **JSON Fields**: Store complex data structures
3. **Many-to-Many Through**: Custom relationship data
4. **Property Methods**: Calculated fields
5. **Custom Validation**: Business logic validation
6. **Database Indexes**: Performance optimization
7. **Related Names**: Clear reverse relationships

---

## 4. Authentication System

### 🎯 Learning Objectives
- Implement JWT authentication
- Create secure user registration
- Handle password reset flows
- Add social authentication

### Step 4.1: JWT Configuration

In `promptcraft/settings/base.py`, add:

```python
# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'ai_requests': '50/hour',
    }
}
```

### Step 4.2: Custom User Serializers

**apps/users/serializers.py**:

```python
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    
    Handles:
    - Password validation
    - Email uniqueness
    - Username validation
    - Initial user setup
    """
    
    password = serializers.CharField(
        write_only=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        """Create new user with proper password hashing"""
        # Remove password_confirm from validated data
        validated_data.pop('password_confirm', None)
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        
        # Initialize gamification data
        user.credits = 100  # Welcome bonus
        user.level = 1
        user.experience_points = 0
        user.user_rank = 'Prompt Novice'
        user.save()
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    
    Supports login with either:
    - Username and password
    - Email and password
    """
    
    username_or_email = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        """Authenticate user with username/email and password"""
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')

        if username_or_email and password:
            # Try to find user by username or email
            try:
                if '@' in username_or_email:
                    # Email login
                    user = User.objects.get(email=username_or_email)
                    username = user.username
                else:
                    # Username login
                    username = username_or_email
                
                # Authenticate user
                user = authenticate(
                    request=self.context.get('request'),
                    username=username,