# apps/gamification/services.py
from django.utils import timezone
from django.db import transaction
from .models import Achievement, UserAchievement, DailyChallenge, UserDailyChallenge, CreditTransaction
import logging

logger = logging.getLogger(__name__)

class GamificationService:
    @staticmethod
    def award_credits(user, amount, reason, transaction_type='bonus', related_object=None):
        """Award credits to user and create transaction record"""
        with transaction.atomic():
            # Update user credits
            user.credits += amount
            user.save(update_fields=['credits'])
            
            # Create transaction record
            transaction_data = {
                'user': user,
                'amount': amount,
                'transaction_type': transaction_type,
                'description': reason,
            }
            
            if related_object:
                transaction_data['related_object_type'] = related_object.__class__.__name__.lower()
                transaction_data['related_object_id'] = str(related_object.id)
            
            CreditTransaction.objects.create(**transaction_data)
            
            logger.info(f"Awarded {amount} credits to user {user.username}: {reason}")
            return user.credits
    
    @staticmethod
    def spend_credits(user, amount, reason, transaction_type='spent_ai'):
        """Spend user credits with validation"""
        if user.credits < amount:
            raise ValueError("Insufficient credits")
        
        with transaction.atomic():
            user.credits -= amount
            user.save(update_fields=['credits'])
            
            CreditTransaction.objects.create(
                user=user,
                amount=-amount,  # Negative for spending
                transaction_type=transaction_type,
                description=reason,
            )
            
            logger.info(f"User {user.username} spent {amount} credits: {reason}")
            return user.credits
    
    @staticmethod
    def check_achievements(user):
        """Check and unlock achievements for user"""
        unlocked = []
        achievements = Achievement.objects.filter(is_active=True)
        
        for achievement in achievements:
            # Skip if already unlocked
            if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                continue
            
            # Check if user meets requirements
            if GamificationService._check_achievement_requirement(user, achievement):
                user_achievement = UserAchievement.objects.create(
                    user=user,
                    achievement=achievement,
                    progress_value=achievement.requirement_value
                )
                unlocked.append(user_achievement)
                
                logger.info(f"User {user.username} unlocked achievement: {achievement.name}")
        
        return unlocked
    
    @staticmethod
    def _check_achievement_requirement(user, achievement):
        """Check if user meets specific achievement requirement"""
        req_type = achievement.requirement_type
        req_value = achievement.requirement_value
        
        if req_type == 'templates_created':
            return user.templates_created >= req_value
        elif req_type == 'templates_completed':
            return user.templates_completed >= req_value
        elif req_type == 'daily_streak':
            return user.daily_streak >= req_value
        elif req_type == 'level':
            return user.level >= req_value
        elif req_type == 'credits_earned':
            total_earned = CreditTransaction.objects.filter(
                user=user, amount__gt=0
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            return total_earned >= req_value
        
        return False
    
    @staticmethod
    def update_daily_streak(user):
        """Update user's daily streak"""
        today = timezone.now().date()
        
        if user.last_login_date == today:
            # Already logged in today
            return user.daily_streak
        elif user.last_login_date == today - timezone.timedelta(days=1):
            # Consecutive day
            user.daily_streak += 1
        else:
            # Streak broken
            user.daily_streak = 1
        
        user.last_login_date = today
        user.save(update_fields=['daily_streak', 'last_login_date'])
        
        # Award streak bonus credits
        if user.daily_streak % 7 == 0:  # Weekly bonus
            bonus_credits = user.daily_streak * 2
            GamificationService.award_credits(
                user, bonus_credits, 
                f"Weekly streak bonus: {user.daily_streak} days",
                'bonus'
            )
        
        # Check for streak achievements
        GamificationService.check_achievements(user)
        
        return user.daily_streak
    
    @staticmethod
    def update_daily_challenge_progress(user, challenge_type, value=1):
        """Update progress on daily challenges"""
        today = timezone.now().date()
        challenges = DailyChallenge.objects.filter(
            date=today, 
            challenge_type=challenge_type,
            is_active=True
        )
        
        for challenge in challenges:
            user_challenge, created = UserDailyChallenge.objects.get_or_create(
                user=user,
                challenge=challenge,
                defaults={'progress_value': 0}
            )
            
            if not user_challenge.is_completed:
                user_challenge.progress_value += value
                
                # Check if completed
                if user_challenge.progress_value >= challenge.target_value:
                    user_challenge.is_completed = True
                    user_challenge.completed_at = timezone.now()
                    
                    # Award rewards
                    GamificationService.award_credits(
                        user, challenge.credits_reward,
                        f"Daily challenge completed: {challenge.title}",
                        'earned_challenge'
                    )
                    
                    user.experience_points += challenge.experience_reward
                    user.save(update_fields=['experience_points'])
                
                user_challenge.save()


# apps/analytics/services.py
from django.utils import timezone
from .models import AnalyticsEvent, UserSession, PerformanceMetric
import uuid

class AnalyticsService:
    @staticmethod
    def track_event(user=None, event_name=None, category='general', properties=None, 
                   session_id=None, device_info=None):
        """Track analytics event"""
        if not event_name:
            return
        
        AnalyticsEvent.objects.create(
            user=user,
            event_name=event_name,
            category=category,
            properties=properties or {},
            session_id=session_id or str(uuid.uuid4()),
            device_info=device_info or {}
        )
    
    @staticmethod
    def start_session(user=None, device_info=None):
        """Start a new user session"""
        session_id = str(uuid.uuid4())
        
        UserSession.objects.create(
            session_id=session_id,
            user=user,
            device_info=device_info or {}
        )
        
        return session_id
    
    @staticmethod
    def end_session(session_id):
        """End a user session"""
        try:
            session = UserSession.objects.get(session_id=session_id)
            session.end_time = timezone.now()
            session.duration_seconds = (session.end_time - session.start_time).total_seconds()
            session.save()
        except UserSession.DoesNotExist:
            pass
    
    @staticmethod
    def record_performance_metric(metric_name, value, unit, user=None, metadata=None):
        """Record performance metric"""
        PerformanceMetric.objects.create(
            metric_name=metric_name,
            value=value,
            unit=unit,
            user=user,
            metadata=metadata or {}
        )


# apps/ai_services/services.py
import openai
import anthropic
from django.conf import settings
from .models import AIInsight, AIInteraction
from apps.analytics.services import AnalyticsService
import time
import logging

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def analyze_template(template, user):
        """Analyze template with AI for optimization suggestions"""
        start_time = time.time()
        
        try:
            # Use OpenAI for template analysis
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = f"""
            Analyze this prompt template for optimization opportunities:
            
            Title: {template.title}
            Description: {template.description}
            Content: {template.template_content}
            
            Provide suggestions for:
            1. Clarity improvements
            2. Field organization
            3. User experience enhancements
            4. Effectiveness for AI interactions
            
            Return as JSON with suggestions array.
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            # Record AI interaction
            AIInteraction.objects.create(
                user=user,
                interaction_type='template_analysis',
                ai_service='openai',
                request_data={'template_id': str(template.id)},
                response_data={'content': response.choices[0].message.content},
                response_time_ms=response_time,
                was_successful=True,
                tokens_used=response.usage.total_tokens
            )
            
            # Create AI insight
            insight = AIInsight.objects.create(
                user=user,
                related_template=template,
                insight_type='optimization',
                title='Template Optimization Suggestions',
                description='AI-generated suggestions to improve your template',
                confidence=0.8,
                ai_model='gpt-3.5-turbo',
                processing_time_ms=response_time
            )
            
            return {
                'insight_id': insight.id,
                'suggestions': response.choices[0].message.content,
                'confidence': 0.8,
                'processing_time_ms': response_time
            }
            
        except Exception as e:
            logger.error(f"AI template analysis failed: {e}")
            
            # Record failed interaction
            AIInteraction.objects.create(
                user=user,
                interaction_type='template_analysis',
                ai_service='openai',
                request_data={'template_id': str(template.id)},
                response_time_ms=int((time.time() - start_time) * 1000),
                was_successful=False,
                error_message=str(e)
            )
            
            return {
                'error': 'AI analysis temporarily unavailable',
                'message': 'Please try again later'
            }
    
    @staticmethod
    def generate_template_suggestions(user_preferences, usage_history):
        """Generate personalized template recommendations"""
        # This would use ML models to analyze user behavior and suggest templates
        # For now, return mock data
        return {
            'recommendations': [
                {
                    'template_id': 'suggested_1',
                    'title': 'Meeting Summary Template',
                    'confidence': 0.85,
                    'reasoning': 'Based on your frequent use of business templates'
                }
            ]
        }


# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create logs directory
RUN mkdir -p /app/logs

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "promptcraft.wsgi:application"]


# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: promptcraft
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=1
      - SECRET_KEY=your-secret-key-here
      - DATABASE_URL=postgres://postgres:postgres@db:5432/promptcraft
      - REDIS_URL=redis://redis:6379/0

  celery:
    build: .
    command: celery -A promptcraft worker -l info
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=1
      - SECRET_KEY=your-secret-key-here
      - DATABASE_URL=postgres://postgres:postgres@db:5432/promptcraft
      - REDIS_URL=redis://redis:6379/0

volumes:
  postgres_data:


# .env.example
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=promptcraft
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@promptcraft.app

# AWS S3 (if using for media files)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Analytics
ENABLE_ANALYTICS=True
ANALYTICS_RETENTION_DAYS=90


# apps/core/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.templates.models import Template, TemplateCategory, PromptField, FieldType
from apps.gamification.models import Achievement, DailyChallenge
from django.utils import timezone
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for development'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample user
        user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'email': 'demo@promptcraft.app',
                'first_name': 'Demo',
                'last_name': 'User',
                'credits': 500,
                'level': 3,
                'experience_points': 250,
                'user_rank': 'Prompt Apprentice'
            }
        )
        
        # Create categories
        categories = [
            {'name': 'Business Strategy', 'slug': 'business', 'color': '#6366F1', 'icon': 'business'},
            {'name': 'Creative Content', 'slug': 'creative', 'color': '#EC4899', 'icon': 'palette'},
            {'name': 'Software Engineering', 'slug': 'engineering', 'color': '#10B981', 'icon': 'code'},
            {'name': 'Education', 'slug': 'education', 'color': '#F59E0B', 'icon': 'school'},
            {'name': 'Marketing', 'slug': 'marketing', 'color': '#EF4444', 'icon': 'campaign'},
        ]
        
        for cat_data in categories:
            TemplateCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
        
        # Create sample templates
        business_cat = TemplateCategory.objects.get(slug='business')
        
        template, created = Template.objects.get_or_create(
            title='Business Plan Generator',
            defaults={
                'description': 'Create a comprehensive business plan with AI assistance',
                'category': business_cat,
                'author': user,
                'template_content': '''Create a business plan for:

Company Name: {{company_name}}
Industry: {{industry}}
Target Market: {{target_market}}
Business Model: {{business_model}}

Executive Summary:
{{executive_summary}}

Market Analysis:
{{market_analysis}}

Financial Projections:
{{financial_projections}}

Please provide a detailed business plan based on this information.''',
                'is_public': True,
                'is_featured': True,
                'popularity_score': 85.5
            }
        )
        
        if created:
            # Create fields for the template
            fields_data = [
                {'label': 'Company Name', 'placeholder': 'Enter your company name', 'field_type': FieldType.TEXT, 'is_required': True, 'order': 0},
                {'label': 'Industry', 'placeholder': 'Select industry', 'field_type': FieldType.DROPDOWN, 'options': ['Technology', 'Healthcare', 'Finance', 'Retail', 'Manufacturing'], 'is_required': True, 'order': 1},
                {'label': 'Target Market', 'placeholder': 'Describe your target market', 'field_type': FieldType.TEXTAREA, 'is_required': True, 'order': 2},
                {'label': 'Business Model', 'placeholder': 'Describe your business model', 'field_type': FieldType.TEXTAREA, 'is_required': True, 'order': 3},
                {'label': 'Executive Summary', 'placeholder': 'Brief executive summary', 'field_type': FieldType.TEXTAREA, 'order': 4},
                {'label': 'Market Analysis', 'placeholder': 'Market analysis details', 'field_type': FieldType.TEXTAREA, 'order': 5},
                {'label': 'Financial Projections', 'placeholder': 'Financial projections', 'field_type': FieldType.TEXTAREA, 'order': 6},
            ]
            
            for field_data in fields_data:
                field = PromptField.objects.create(**field_data)
                template.fields.add(field)
        
        # Create achievements
        achievements = [
            {
                'name': 'First Steps',
                'description': 'Create your first template',
                'requirement_type': 'templates_created',
                'requirement_value': 1,
                'credits_reward': 50,
                'experience_reward': 25,
                'category': 'getting_started',
                'rarity': 'common'
            },
            {
                'name': 'Template Master',
                'description': 'Create 10 templates',
                'requirement_type': 'templates_created',
                'requirement_value': 10,
                'credits_reward': 200,
                'experience_reward': 100,
                'category': 'creation',
                'rarity': 'rare'
            },
            {
                'name': 'Streak Champion',
                'description': 'Maintain a 7-day login streak',
                'requirement_type': 'daily_streak',
                'requirement_value': 7,
                'credits_reward': 100,
                'experience_reward': 50,
                'category': 'engagement',
                'rarity': 'epic'
            }
        ]
        
        for ach_data in achievements:
            Achievement.objects.get_or_create(
                name=ach_data['name'],
                defaults=ach_data
            )
        
        # Create daily challenge
        today = timezone.now().date()
        DailyChallenge.objects.get_or_create(
            date=today,
            challenge_type='complete_templates',
            defaults={
                'title': 'Complete 3 Templates',
                'description': 'Generate prompts using 3 different templates today',
                'target_value': 3,
                'credits_reward': 75,
                'experience_reward': 40,
                'is_active': True
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )


# manage.py command to run the setup
"""
To set up the project:

1. Clone the repository
2. Copy .env.example to .env and fill in your values
3. Run: docker-compose up --build
4. In another terminal: docker-compose exec web python manage.py migrate
5. Create sample data: docker-compose exec web python manage.py create_sample_data
6. Create superuser: docker-compose exec web python manage.py createsuperuser

For production deployment:
1. Set DEBUG=False in environment
2. Configure proper database and Redis
3. Set up proper secret key
4. Configure static/media file serving
5. Set up SSL/HTTPS
6. Configure domain in ALLOWED_HOSTS
"""
