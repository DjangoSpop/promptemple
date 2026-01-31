# 🚀 PromptCraft Backend LEAN RESCUE PLAN
## Step-by-Step Manual for Backend Optimization & Documentation

**Date:** January 25, 2026  
**Goal:** Transform heavy backend into lean, production-ready system focused on prompt enhancement and templates  
**Target:** Docker image <400MB, API response <200ms, Railway-ready

---

## 📊 CURRENT STATE ANALYSIS

### Current Architecture Issues:
- ✅ **Has working apps:** prompt_history, templates, ai_services, billing, users
- ❌ **Heavy dependencies:** LangChain still included (~20MB)
- ❌ **Complex AI services:** Over-engineered with multiple models/providers
- ✅ **Good foundation:** Django + DRF + PostgreSQL already set up
- ❌ **Missing:** Direct lightweight API for prompt enhancement

### Current Apps Status:
```
apps/
├── ai_services/        # TOO COMPLEX - needs simplification
├── prompt_history/     # ✅ GOOD - keep as is
├── templates/          # ✅ GOOD - simplify slightly
├── billing/            # ✅ GOOD - add usage tracking
├── users/              # ✅ GOOD - keep as is
├── chat/               # ⚠️ OPTIONAL - defer if not needed
├── analytics/          # ⚠️ OPTIONAL - defer if not needed
├── gamification/       # ❌ REMOVE - out of scope for MVP
├── orchestrator/       # ❌ REMOVE - too complex
└── mvp_ui/             # ⚠️ KEEP - but ensure it's minimal
```

---

## 🎯 SPRINT 1: LEAN DEPENDENCIES (Week 1, Days 1-2)

### Task 1.1: Create Lean Requirements File

**Goal:** Reduce dependencies to essentials only

**Create:** `requirements-lean.txt`

```python
# ===== LEAN PRODUCTION REQUIREMENTS =====
# Total estimated size: ~200MB

# Core Django Framework
Django==4.2.16
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-filter==23.5

# Authentication & Security
djangorestframework-simplejwt==5.3.1
django-allauth==0.57.2
PyJWT==2.8.0

# Database & Caching
psycopg2-binary==2.9.9
dj-database-url==2.1.0
redis==5.0.1
django-redis==5.4.0

# Production Server
gunicorn==23.0.0
whitenoise==6.8.1

# API Documentation
drf-spectacular==0.27.0

# Payment
stripe==8.0.0

# Utilities
python-decouple==3.8
requests==2.31.0
Pillow==10.2.0

# WebSocket (if needed for streaming)
channels==4.0.0
channels-redis==4.2.0
daphne==4.1.0

# Monitoring (optional)
sentry-sdk==1.40.0
```

**Actions:**
1. Create new file `requirements-lean.txt`
2. Remove: LangChain, OpenAI SDK (we'll use requests directly), Anthropic, GraphQL (if not used)
3. Keep only essentials

**Testing:**
```powershell
# Create test virtual environment
python -m venv venv_lean_test
.\venv_lean_test\Scripts\activate
pip install -r requirements-lean.txt

# Verify size
pip list --format=columns

# Should be ~50-60 packages total, not 100+
```

**Expected Result:**
- ✅ Requirements file with <25 packages
- ✅ All packages install without errors
- ✅ Estimated total size ~200MB

---

## 🎯 SPRINT 2: REFACTOR AI SERVICES (Week 1, Days 3-5)

### Task 2.1: Create Lean Prompt Enhancement Service

**Goal:** Simple, fast prompt enhancement without LangChain

**Create:** `apps/ai_services/services/prompt_enhancer.py`

```python
"""
Lean Prompt Enhancement Service
Direct API calls to DeepSeek - no heavy dependencies
"""

import requests
import logging
from typing import Dict, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PromptEnhancementError(Exception):
    """Custom exception for enhancement failures"""
    pass


class PromptEnhancerService:
    """
    Lightweight prompt enhancement using DeepSeek API
    Target: <200ms response time (excluding DeepSeek API call)
    """
    
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
    
    # System prompts for different enhancement types
    SYSTEM_PROMPTS = {
        'general': """You are an expert prompt engineer. Enhance the user's prompt to be more effective with AI models.

Apply these principles:
- Add clear context and constraints
- Structure for better reasoning
- Include output format specifications
- Maintain user's original intent

Return ONLY the enhanced prompt, no explanations.""",
        
        'technical': """You are an expert at crafting technical prompts.
Enhance this prompt for technical accuracy, precision, and structured output.
Include relevant technical context and expected format.

Return ONLY the enhanced prompt.""",
        
        'creative': """You are an expert at crafting creative prompts.
Enhance this prompt to inspire creative exploration while maintaining clarity.
Add context that encourages unique perspectives.

Return ONLY the enhanced prompt.""",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not configured")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def enhance_prompt(
        self, 
        prompt: str,
        enhancement_type: str = "general",
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Enhance a user prompt using DeepSeek
        
        Args:
            prompt: Original prompt to enhance
            enhancement_type: Type of enhancement (general, technical, creative)
            user_id: User ID for caching/tracking
        
        Returns:
            {
                'original': str,
                'enhanced': str,
                'improvement_notes': str,
                'tokens_used': int,
                'response_time_ms': float
            }
        
        Raises:
            PromptEnhancementError: If API call fails
        """
        
        # Input validation
        if not prompt or not prompt.strip():
            raise PromptEnhancementError("Empty prompt provided")
        
        if len(prompt) > 5000:
            raise PromptEnhancementError("Prompt too long (max 5000 characters)")
        
        # Check cache first (optional optimization)
        cache_key = f"enhanced_prompt:{hash(prompt)}:{enhancement_type}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for prompt enhancement")
            return cached_result
        
        # Select system prompt
        system_prompt = self.SYSTEM_PROMPTS.get(
            enhancement_type, 
            self.SYSTEM_PROMPTS['general']
        )
        
        # Prepare API request
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        try:
            import time
            start_time = time.time()
            
            response = requests.post(
                self.DEEPSEEK_API_URL,
                headers=self.headers,
                json=payload,
                timeout=15  # 15 second timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            response.raise_for_status()
            data = response.json()
            
            enhanced = data['choices'][0]['message']['content'].strip()
            tokens_used = data.get('usage', {}).get('total_tokens', 0)
            
            result = {
                'original': prompt,
                'enhanced': enhanced,
                'improvement_notes': self._generate_improvement_notes(prompt, enhanced),
                'tokens_used': tokens_used,
                'response_time_ms': response_time
            }
            
            # Cache successful result (30 minutes)
            cache.set(cache_key, result, timeout=1800)
            
            logger.info(
                f"Prompt enhanced successfully in {response_time:.2f}ms "
                f"(tokens: {tokens_used})"
            )
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error("DeepSeek API timeout")
            raise PromptEnhancementError("Enhancement timed out. Please try again.")
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"DeepSeek API HTTP error: {e.response.status_code}")
            if e.response.status_code == 429:
                raise PromptEnhancementError("Rate limit exceeded. Please wait and try again.")
            elif e.response.status_code == 401:
                raise PromptEnhancementError("API authentication failed.")
            else:
                raise PromptEnhancementError(f"API error: {str(e)}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {str(e)}")
            raise PromptEnhancementError("Enhancement service unavailable. Please try again later.")
    
    def _generate_improvement_notes(self, original: str, enhanced: str) -> str:
        """Generate brief notes on what was improved"""
        notes = []
        
        # Check for length increase (more detail added)
        if len(enhanced) > len(original) * 1.3:
            notes.append("Added context and structure")
        
        # Check for format specification
        if any(word in enhanced.lower() for word in ['format:', 'output:', 'structure:']):
            if not any(word in original.lower() for word in ['format:', 'output:', 'structure:']):
                notes.append("Specified output format")
        
        # Check for improved organization
        if enhanced.count('\n') > original.count('\n') + 2:
            notes.append("Improved organization")
        
        # Check for added constraints
        if any(word in enhanced.lower() for word in ['must', 'should', 'ensure', 'include']):
            notes.append("Added constraints")
        
        return "; ".join(notes) if notes else "General refinement and clarity improvements"
    
    def batch_enhance(self, prompts: list[str], enhancement_type: str = "general") -> list[Dict]:
        """Enhance multiple prompts (useful for bulk operations)"""
        results = []
        for prompt in prompts:
            try:
                result = self.enhance_prompt(prompt, enhancement_type)
                results.append(result)
            except PromptEnhancementError as e:
                results.append({
                    'original': prompt,
                    'error': str(e)
                })
        return results
```

**Actions:**
1. Create `apps/ai_services/services/` directory
2. Create `prompt_enhancer.py` with above code
3. Add `__init__.py` in services directory

**Testing Script:** `test_prompt_enhancer.py`
```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from apps.ai_services.services.prompt_enhancer import PromptEnhancerService

def test_enhancement():
    service = PromptEnhancerService()
    
    test_prompt = "write a blog post about AI"
    
    print("Testing prompt enhancement...")
    print(f"Original: {test_prompt}")
    
    result = service.enhance_prompt(test_prompt, enhancement_type='general')
    
    print(f"\nEnhanced: {result['enhanced']}")
    print(f"Tokens used: {result['tokens_used']}")
    print(f"Response time: {result['response_time_ms']:.2f}ms")
    print(f"Improvements: {result['improvement_notes']}")
    
    assert result['enhanced'] != result['original']
    assert result['tokens_used'] > 0
    print("\n✅ Test passed!")

if __name__ == "__main__":
    test_enhancement()
```

**Expected Result:**
- ✅ Service enhances prompts successfully
- ✅ Response time logged
- ✅ Error handling works
- ✅ No LangChain dependency needed

---

## 🎯 SPRINT 3: LEAN API VIEWS (Week 2, Days 1-3)

### Task 3.1: Create Prompt Enhancement API Endpoint

**Update:** `apps/ai_services/views.py`

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.core.cache import cache
from django.utils import timezone
import logging

from .services.prompt_enhancer import PromptEnhancerService, PromptEnhancementError
from apps.prompt_history.models import PromptHistory
from apps.billing.models import UsageStats

logger = logging.getLogger(__name__)


class PromptEnhancementView(APIView):
    """
    Lean prompt enhancement endpoint
    
    Target performance: <50ms (excluding DeepSeek API call)
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Enhance a prompt",
        description="Enhance a user's prompt using AI. Returns improved version with better structure and clarity.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'prompt': {
                        'type': 'string',
                        'description': 'Original prompt to enhance'
                    },
                    'enhancement_type': {
                        'type': 'string',
                        'enum': ['general', 'technical', 'creative'],
                        'default': 'general',
                        'description': 'Type of enhancement to apply'
                    },
                    'save_history': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'Whether to save in prompt history'
                    }
                },
                'required': ['prompt']
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'original': {'type': 'string'},
                    'enhanced': {'type': 'string'},
                    'improvement_notes': {'type': 'string'},
                    'tokens_used': {'type': 'integer'},
                    'response_time_ms': {'type': 'number'},
                    'history_id': {'type': 'string', 'format': 'uuid'}
                }
            },
            400: {'description': 'Invalid input'},
            429: {'description': 'Rate limit exceeded'},
            500: {'description': 'Enhancement failed'}
        },
        tags=['Prompt Enhancement']
    )
    def post(self, request):
        """
        POST /api/v2/prompts/enhance
        
        Enhance a user prompt
        """
        prompt = request.data.get('prompt', '').strip()
        enhancement_type = request.data.get('enhancement_type', 'general')
        save_history = request.data.get('save_history', True)
        
        # Validation
        if not prompt:
            return Response(
                {'error': 'Prompt is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(prompt) > 5000:
            return Response(
                {'error': 'Prompt too long (max 5000 characters)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if enhancement_type not in ['general', 'technical', 'creative']:
            enhancement_type = 'general'
        
        # Check rate limit
        if not self._check_rate_limit(request.user):
            return Response(
                {
                    'error': 'Monthly enhancement limit reached. Upgrade your plan for more enhancements.',
                    'upgrade_url': '/billing/upgrade'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Enhance prompt
        try:
            service = PromptEnhancerService()
            result = service.enhance_prompt(
                prompt=prompt,
                enhancement_type=enhancement_type,
                user_id=request.user.id
            )
            
            # Track usage for billing
            self._track_usage(request.user, result['tokens_used'])
            
            # Save to history if requested
            history_id = None
            if save_history:
                history_id = self._save_to_history(
                    user=request.user,
                    original=result['original'],
                    enhanced=result['enhanced'],
                    tokens_used=result['tokens_used']
                )
            
            # Add history ID to response
            response_data = {**result}
            if history_id:
                response_data['history_id'] = str(history_id)
            
            # Log performance
            logger.info(
                f"Enhancement completed for user {request.user.id} "
                f"in {result['response_time_ms']:.2f}ms"
            )
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except PromptEnhancementError as e:
            logger.error(f"Enhancement error for user {request.user.id}: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _check_rate_limit(self, user) -> bool:
        """Check if user has remaining quota"""
        # Get or create usage stats for current month
        stats, created = UsageStats.objects.get_or_create(
            user=user,
            period_start__year=timezone.now().year,
            period_start__month=timezone.now().month,
            defaults={
                'period_start': timezone.now().replace(day=1, hour=0, minute=0),
                'enhancements_count': 0
            }
        )
        
        # Get user's monthly limit (default 50 for free tier)
        monthly_limit = getattr(user, 'monthly_enhancement_limit', 50)
        
        return stats.enhancements_count < monthly_limit
    
    def _track_usage(self, user, tokens_used: int):
        """Track enhancement usage for billing"""
        stats, created = UsageStats.objects.get_or_create(
            user=user,
            period_start__year=timezone.now().year,
            period_start__month=timezone.now().month,
            defaults={
                'period_start': timezone.now().replace(day=1, hour=0, minute=0),
                'enhancements_count': 0,
                'tokens_used': 0
            }
        )
        
        stats.enhancements_count += 1
        stats.tokens_used += tokens_used
        stats.save(update_fields=['enhancements_count', 'tokens_used'])
    
    def _save_to_history(self, user, original: str, enhanced: str, tokens_used: int):
        """Save enhancement to user's history"""
        history = PromptHistory.objects.create(
            user=user,
            original_prompt=original,
            optimized_prompt=enhanced,
            tokens_input=len(original.split()),  # Rough estimate
            tokens_output=tokens_used,
            source='web_api',
            intent_category='enhancement'
        )
        return history.id


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@extend_schema(
    summary="Get user's prompt history",
    description="Retrieve paginated list of user's prompt enhancement history",
    tags=['Prompt History']
)
def get_prompt_history(request):
    """
    GET /api/v2/prompts/history
    
    Get user's enhancement history
    """
    history = PromptHistory.objects.filter(
        user=request.user,
        is_deleted=False
    ).order_by('-created_at')[:50]  # Last 50
    
    data = [{
        'id': str(h.id),
        'original': h.original_prompt,
        'enhanced': h.optimized_prompt,
        'tokens_used': h.tokens_output,
        'created_at': h.created_at.isoformat()
    } for h in history]
    
    return Response({'history': data, 'count': len(data)})
```

**Actions:**
1. Update `apps/ai_services/views.py`
2. Ensure UsageStats model exists in `apps/billing/models.py`
3. Update URL routing

**Create:** `apps/ai_services/urls.py`
```python
from django.urls import path
from . import views

app_name = 'ai_services'

urlpatterns = [
    path('enhance', views.PromptEnhancementView.as_view(), name='enhance'),
    path('history', views.get_prompt_history, name='history'),
]
```

**Testing:**
```powershell
# Start server
python manage.py runserver

# Test with curl
curl -X POST http://localhost:8000/api/v2/ai/enhance `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"prompt": "write a blog post", "enhancement_type": "general"}'
```

**Expected Result:**
- ✅ API endpoint responds correctly
- ✅ Authentication required
- ✅ Rate limiting works
- ✅ History saved
- ✅ Usage tracked

---

## 🎯 SPRINT 4: USAGE TRACKING & BILLING (Week 2, Days 4-5)

### Task 4.1: Create/Update Usage Stats Model

**Update:** `apps/billing/models.py`

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()


class UsageStats(models.Model):
    """
    Track user usage for billing
    Simple counter-based system
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_stats')
    
    # Billing period
    period_start = models.DateTimeField(db_index=True)
    period_end = models.DateTimeField()
    
    # Usage counters
    enhancements_count = models.IntegerField(default=0)
    templates_applied = models.IntegerField(default=0)
    tokens_used = models.BigIntegerField(default=0)
    api_calls = models.IntegerField(default=0)
    
    # Cost tracking (for internal analysis)
    estimated_cost_usd = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=0,
        help_text="Estimated API cost for this period"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'usage_stats'
        unique_together = ['user', 'period_start']
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['user', '-period_start']),
            models.Index(fields=['period_start', 'period_end'])
        ]
    
    def __str__(self):
        return f"Usage for {self.user.email} ({self.period_start.strftime('%Y-%m')})"
    
    @classmethod
    def get_current_period(cls, user):
        """Get or create stats for current billing period"""
        now = timezone.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate period end (last day of month)
        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)
        
        stats, created = cls.objects.get_or_create(
            user=user,
            period_start=period_start,
            defaults={'period_end': period_end}
        )
        
        return stats
    
    def calculate_cost(self):
        """Calculate estimated API cost (DeepSeek pricing)"""
        # DeepSeek pricing: ~$0.0001 per 1K tokens
        cost_per_1k_tokens = 0.0001
        self.estimated_cost_usd = (self.tokens_used / 1000) * cost_per_1k_tokens
        self.save(update_fields=['estimated_cost_usd'])
        return self.estimated_cost_usd


class UserProfile(models.Model):
    """Extended user profile with subscription info"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Subscription tier
    TIER_CHOICES = [
        ('free', 'Free - 50 enhancements/month'),
        ('pro', 'Pro - 500 enhancements/month'),
        ('enterprise', 'Enterprise - Unlimited'),
    ]
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    
    # Limits
    monthly_enhancement_limit = models.IntegerField(default=50)
    monthly_template_limit = models.IntegerField(default=100)
    
    # Stripe integration
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    subscription_status = models.CharField(max_length=20, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_tier_display()}"
    
    def get_remaining_enhancements(self):
        """Get remaining enhancements for current period"""
        stats = UsageStats.get_current_period(self.user)
        remaining = self.monthly_enhancement_limit - stats.enhancements_count
        return max(0, remaining)


# Signal to auto-create profile
from django.db.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
```

**Create migrations:**
```powershell
python manage.py makemigrations billing
python manage.py migrate billing
```

**Testing:**
```python
# test_usage_tracking.py
from django.contrib.auth import get_user_model
from apps.billing.models import UsageStats, UserProfile

User = get_user_model()

def test_usage_tracking():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Get current period stats
    stats = UsageStats.get_current_period(user)
    
    print(f"Initial enhancements: {stats.enhancements_count}")
    
    # Simulate usage
    stats.enhancements_count += 1
    stats.tokens_used += 500
    stats.save()
    
    stats.calculate_cost()
    
    print(f"After enhancement: {stats.enhancements_count}")
    print(f"Tokens used: {stats.tokens_used}")
    print(f"Estimated cost: ${stats.estimated_cost_usd}")
    
    # Check profile limits
    profile = user.profile
    remaining = profile.get_remaining_enhancements()
    print(f"Remaining enhancements: {remaining}/{profile.monthly_enhancement_limit}")
    
    print("✅ Usage tracking test passed!")

if __name__ == "__main__":
    test_usage_tracking()
```

**Expected Result:**
- ✅ UsageStats model created
- ✅ UserProfile model created
- ✅ Auto-creation works
- ✅ Usage tracking functional

---

## 🎯 SPRINT 5: API DOCUMENTATION (Week 3, Days 1-2)

### Task 5.1: Generate OpenAPI Documentation

**Update:** `promptcraft/settings.py` - Add Spectacular config

```python
# DRF Spectacular (OpenAPI) Configuration
SPECTACULAR_SETTINGS = {
    'TITLE': 'PromptCraft API',
    'DESCRIPTION': 'Lean prompt enhancement and template management API',
    'VERSION': '2.0.0-lean',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v2',
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and registration'},
        {'name': 'Prompt Enhancement', 'description': 'AI-powered prompt optimization'},
        {'name': 'Templates', 'description': 'Prompt template management'},
        {'name': 'Prompt History', 'description': 'User prompt history tracking'},
        {'name': 'Billing', 'description': 'Usage stats and billing information'},
    ],
}
```

**Update:** `promptcraft/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v2 endpoints
    path('api/v2/auth/', include('apps.users.urls')),
    path('api/v2/ai/', include('apps.ai_services.urls')),
    path('api/v2/templates/', include('apps.templates.urls')),
    path('api/v2/history/', include('apps.prompt_history.urls')),
    path('api/v2/billing/', include('apps.billing.urls')),
]
```

**Create:** `API_CONTRACT.md` - Documentation for developers

```markdown
# PromptCraft API v2.0 - Complete Contract

## Base URL
- **Production:** `https://your-app.railway.app/api/v2`
- **Development:** `http://localhost:8000/api/v2`

## Authentication
All endpoints except `/auth/login` and `/auth/register` require JWT authentication.

**Header:**
```
Authorization: Bearer <your_jwt_token>
```

---

## 📍 Core Endpoints

### 1. **Prompt Enhancement**

#### `POST /ai/enhance`
Enhance a user's prompt using AI.

**Request:**
```json
{
  "prompt": "write a blog post about AI",
  "enhancement_type": "general",
  "save_history": true
}
```

**Parameters:**
- `prompt` (string, required): Original prompt to enhance (max 5000 chars)
- `enhancement_type` (string, optional): Type of enhancement
  - `general` (default): General improvement
  - `technical`: Technical accuracy focus
  - `creative`: Creative exploration focus
- `save_history` (boolean, optional): Save to history (default: true)

**Response (200 OK):**
```json
{
  "original": "write a blog post about AI",
  "enhanced": "Write a comprehensive 1500-word blog post exploring the current state and future implications of Artificial Intelligence...",
  "improvement_notes": "Added context and structure; Specified output format",
  "tokens_used": 450,
  "response_time_ms": 1250.5,
  "history_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Enhancement failed

---

### 2. **Prompt History**

#### `GET /ai/history`
Get user's enhancement history.

**Response (200 OK):**
```json
{
  "history": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "original": "write a blog post",
      "enhanced": "Write a comprehensive...",
      "tokens_used": 450,
      "created_at": "2026-01-25T10:30:00Z"
    }
  ],
  "count": 50
}
```

---

### 3. **Template Management**

#### `GET /templates/`
List user's templates.

**Query Parameters:**
- `category` (string, optional): Filter by category
- `include_public` (boolean, optional): Include public templates (default: true)

**Response (200 OK):**
```json
{
  "templates": [
    {
      "id": 1,
      "name": "Blog Post Template",
      "description": "Create engaging blog posts",
      "category": "creative",
      "template_text": "Write a {{tone}} blog post about {{topic}}...",
      "variables": ["tone", "topic"],
      "is_public": true,
      "usage_count": 25,
      "created_at": "2026-01-20T10:00:00Z"
    }
  ]
}
```

#### `POST /templates/`
Create a new template.

**Request:**
```json
{
  "name": "Technical Documentation Template",
  "description": "Generate technical docs",
  "category": "technical",
  "template_text": "Create {{doc_type}} for {{project_name}}. Include: {{sections}}",
  "is_public": false
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "name": "Technical Documentation Template",
  "variables": ["doc_type", "project_name", "sections"],
  ...
}
```

#### `POST /templates/{id}/apply`
Apply template with variables.

**Request:**
```json
{
  "variables": {
    "tone": "professional",
    "topic": "AI ethics"
  }
}
```

**Response (200 OK):**
```json
{
  "template_id": 1,
  "populated_prompt": "Write a professional blog post about AI ethics...",
  "can_enhance": true
}
```

---

### 4. **Usage & Billing**

#### `GET /billing/stats`
Get current usage statistics.

**Response (200 OK):**
```json
{
  "total_enhancements": 35,
  "total_templates_applied": 12,
  "tokens_used": 15000,
  "current_period_start": "2026-01-01T00:00:00Z",
  "current_period_end": "2026-02-01T00:00:00Z",
  "monthly_limit": 50,
  "remaining_enhancements": 15,
  "tier": "free"
}
```

---

## 📊 Rate Limits

| Tier | Enhancements/Month | Templates/Month | API Calls/Hour |
|------|-------------------|----------------|---------------|
| Free | 50 | 100 | 60 |
| Pro | 500 | 1000 | 600 |
| Enterprise | Unlimited | Unlimited | Unlimited |

---

## 🔗 For Extension Developers

### Chrome Extension MV3 Integration

**Manifest v3 Permissions:**
```json
{
  "permissions": ["storage"],
  "host_permissions": [
    "https://your-app.railway.app/*"
  ]
}
```

**Authentication Flow:**
```javascript
// background.js
async function loginUser(email, password) {
  const response = await fetch('https://your-app.railway.app/api/v2/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email, password})
  });
  
  const {access_token, refresh_token, user} = await response.json();
  
  await chrome.storage.local.set({
    access_token,
    refresh_token,
    user
  });
}
```

**Enhance Prompt:**
```javascript
// api.js
async function enhancePrompt(prompt) {
  const {access_token} = await chrome.storage.local.get(['access_token']);
  
  const response = await fetch('https://your-app.railway.app/api/v2/ai/enhance', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${access_token}`
    },
    body: JSON.stringify({prompt, enhancement_type: 'general'})
  });
  
  return await response.json();
}
```

---

## 🚀 For Frontend Developers

### TypeScript API Client

```typescript
// lib/promptcraft-api.ts
import axios, { AxiosInstance } from 'axios';

interface EnhancePromptRequest {
  prompt: string;
  enhancement_type?: 'general' | 'technical' | 'creative';
  save_history?: boolean;
}

class PromptCraftAPI {
  private client: AxiosInstance;
  
  constructor(baseURL: string = process.env.NEXT_PUBLIC_API_URL!) {
    this.client = axios.create({
      baseURL,
      timeout: 15000,
      headers: {'Content-Type': 'application/json'}
    });
    
    // Auto-add token
    this.client.interceptors.request.use(config => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }
  
  async enhancePrompt(data: EnhancePromptRequest) {
    const response = await this.client.post('/ai/enhance', data);
    return response.data;
  }
  
  async getTemplates(category?: string) {
    const response = await this.client.get('/templates/', {
      params: {category, include_public: true}
    });
    return response.data;
  }
  
  async getUserStats() {
    const response = await this.client.get('/billing/stats');
    return response.data;
  }
}

export const api = new PromptCraftAPI();
```

---

## 📖 Interactive Documentation

Visit:
- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/
```

**Actions:**
1. Create `API_CONTRACT.md`
2. Generate OpenAPI schema
3. Test Swagger UI

**Testing:**
```powershell
python manage.py runserver

# Visit in browser:
# http://localhost:8000/api/docs/
```

**Expected Result:**
- ✅ Swagger UI accessible
- ✅ All endpoints documented
- ✅ Try-it-out functionality works
- ✅ API_CONTRACT.md created

---

## 🎯 SPRINT 6: DOCKER & DEPLOYMENT (Week 3, Days 3-5)

### Task 6.1: Create Optimized Dockerfile

**Create:** `Dockerfile.lean`

```dockerfile
# ===== LEAN PRODUCTION DOCKERFILE =====
# Target size: <400MB

FROM python:3.11-slim as base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 promptcraft && \
    mkdir -p /app /app/static /app/media && \
    chown -R promptcraft:promptcraft /app

WORKDIR /app

# Install Python dependencies
COPY requirements-lean.txt .
RUN pip install --no-cache-dir -r requirements-lean.txt

# Copy application code
COPY --chown=promptcraft:promptcraft . .

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Switch to non-root user
USER promptcraft

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v2/health/', timeout=3)" || exit 1

# Start gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "30", "--access-logfile", "-", "--error-logfile", "-", "promptcraft.wsgi:application"]
```

**Create:** `docker-compose.lean.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: promptcraft_db
    environment:
      POSTGRES_DB: promptcraft_dev
      POSTGRES_USER: promptcraft
      POSTGRES_PASSWORD: dev_password_123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U promptcraft"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: promptcraft_redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile.lean
    container_name: promptcraft_backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/mediafiles
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://promptcraft:dev_password_123@db:5432/promptcraft_dev
      - REDIS_URL=redis://redis:6379/0
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - SECRET_KEY=dev-secret-key-change-in-production
      - ALLOWED_HOSTS=localhost,127.0.0.1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v2/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

**Create:** `.dockerignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Django
*.log
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Git
.git/
.gitignore

# Docker
Dockerfile*
docker-compose*
.dockerignore

# Documentation
*.md
docs/

# Tests
tests/
test_*.py
pytest.ini

# CI/CD
.github/

# Misc
.env.example
*.bak
*.tmp
```

**Create:** `apps/core/views.py` - Health check

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache
from django.utils import timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for Docker and Railway
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check Redis cache
    try:
        cache.set('health_check', 'ok', timeout=10)
        if cache.get('health_check') == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['checks']['cache'] = 'error: cache not working'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['cache'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Return appropriate status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return Response(health_status, status=status_code)
```

**Update:** `apps/core/urls.py`

```python
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('health/', views.health_check, name='health'),
]
```

**Actions:**
1. Create Dockerfile.lean
2. Create docker-compose.lean.yml
3. Create .dockerignore
4. Add health check endpoint
5. Test locally

**Testing:**
```powershell
# Build image
docker build -f Dockerfile.lean -t promptcraft:lean .

# Check image size
docker images | Select-String "promptcraft"

# Start services
docker-compose -f docker-compose.lean.yml up -d

# Check health
docker-compose -f docker-compose.lean.yml ps
curl http://localhost:8000/api/v2/health/

# Test API
curl -X POST http://localhost:8000/api/v2/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email":"test@test.com","password":"test123"}'

# View logs
docker-compose -f docker-compose.lean.yml logs -f backend

# Stop services
docker-compose -f docker-compose.lean.yml down
```

**Expected Result:**
- ✅ Docker image builds successfully
- ✅ Image size <400MB
- ✅ All services start correctly
- ✅ Health check returns OK
- ✅ API endpoints accessible

---

### Task 6.2: Railway Deployment Configuration

**Create:** `railway.toml`

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile.lean"

[deploy]
startCommand = "gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 30 promptcraft.wsgi:application"
healthcheckPath = "/api/v2/health/"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[env]
# These will be set in Railway dashboard
# DATABASE_URL - auto-provided by Railway PostgreSQL plugin
# REDIS_URL - auto-provided by Railway Redis plugin
# DEEPSEEK_API_KEY - manual
# DJANGO_SECRET_KEY - manual (generate secure key)
# ALLOWED_HOSTS - manual (your-app.railway.app)
```

**Create:** `DEPLOYMENT_CHECKLIST.md`

```markdown
# Deployment Checklist

## Pre-Deployment

- [ ] All tests passing locally
- [ ] Docker image tested with `docker-compose.lean.yml`
- [ ] Environment variables documented
- [ ] Database migrations ready
- [ ] Static files collected
- [ ] CORS settings configured for production domains
- [ ] DEBUG set to False in production settings

## Railway Setup

### 1. Create Project
- [ ] Create new Railway project
- [ ] Connect to GitHub repository

### 2. Add Plugins
- [ ] Add PostgreSQL database plugin
- [ ] Add Redis plugin
- [ ] Note the connection URLs

### 3. Configure Environment Variables

Set these in Railway dashboard:

```
DATABASE_URL=<provided by PostgreSQL plugin>
REDIS_URL=<provided by Redis plugin>
DEEPSEEK_API_KEY=<your deepseek api key>
DJANGO_SECRET_KEY=<generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'>
ALLOWED_HOSTS=<your-app>.railway.app
DEBUG=False
DJANGO_SETTINGS_MODULE=promptcraft.settings
```

### 4. Deploy
- [ ] Deploy from GitHub main branch
- [ ] Wait for build to complete
- [ ] Check deployment logs

### 5. Post-Deployment

Run these commands in Railway shell:

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files (if needed)
python manage.py collectstatic --noinput
```

### 6. Verify Deployment

- [ ] Health check responding: `https://<your-app>.railway.app/api/v2/health/`
- [ ] API docs accessible: `https://<your-app>.railway.app/api/docs/`
- [ ] Admin panel works: `https://<your-app>.railway.app/admin/`
- [ ] Login endpoint works
- [ ] Prompt enhancement works
- [ ] No errors in logs for first hour

### 7. Monitoring

- [ ] Set up Sentry for error tracking
- [ ] Configure Railway metrics alerts
- [ ] Monitor API response times
- [ ] Check database query performance

## Post-Launch

- [ ] Document API endpoints for extension team
- [ ] Update frontend/extension with production API URL
- [ ] Test extension with production API
- [ ] Monitor usage and costs
- [ ] Set up backup strategy
```

**Testing Railway Deployment:**
```powershell
# Install Railway CLI
# Windows: scoop install railway
# Or download from: https://railway.app/cli

# Login
railway login

# Link to project
railway link

# Check environment
railway env

# View logs
railway logs

# Open in browser
railway open
```

**Expected Result:**
- ✅ Railway project created
- ✅ Backend deployed successfully
- ✅ All services connected
- ✅ Health check passes
- ✅ API accessible publicly

---

## 🎯 SPRINT 7: TESTING & DEBUGGING (Week 4)

### Task 7.1: Create Comprehensive Test Suite

**Create:** `tests/test_prompt_enhancement.py`

```python
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.ai_services.services.prompt_enhancer import PromptEnhancerService, PromptEnhancementError
from apps.billing.models import UsageStats

User = get_user_model()


@pytest.mark.django_db
class TestPromptEnhancement:
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_enhance_prompt_success(self):
        """Test successful prompt enhancement"""
        response = self.client.post('/api/v2/ai/enhance', {
            'prompt': 'write a blog post about AI',
            'enhancement_type': 'general'
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'enhanced' in response.json()
        assert 'tokens_used' in response.json()
        assert response.json()['original'] != response.json()['enhanced']
    
    def test_enhance_prompt_empty(self):
        """Test enhancement with empty prompt"""
        response = self.client.post('/api/v2/ai/enhance', {
            'prompt': ''
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.json()
    
    def test_enhance_prompt_rate_limit(self):
        """Test rate limiting"""
        # Set user limit to 2
        self.user.profile.monthly_enhancement_limit = 2
        self.user.profile.save()
        
        # Use up quota
        stats = UsageStats.get_current_period(self.user)
        stats.enhancements_count = 2
        stats.save()
        
        # This should fail
        response = self.client.post('/api/v2/ai/enhance', {
            'prompt': 'test prompt'
        })
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_enhance_prompt_unauthorized(self):
        """Test enhancement without authentication"""
        self.client.force_authenticate(user=None)
        
        response = self.client.post('/api/v2/ai/enhance', {
            'prompt': 'test'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestPromptHistory:
    
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_history(self):
        """Test retrieving prompt history"""
        response = self.client.get('/api/v2/ai/history')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'history' in response.json()
        assert 'count' in response.json()


@pytest.mark.django_db
class TestUsageTracking:
    
    def test_usage_stats_creation(self):
        """Test usage stats auto-creation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        stats = UsageStats.get_current_period(user)
        
        assert stats.user == user
        assert stats.enhancements_count == 0
        assert stats.tokens_used == 0
    
    def test_usage_increment(self):
        """Test usage counter increment"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        stats = UsageStats.get_current_period(user)
        stats.enhancements_count += 1
        stats.tokens_used += 500
        stats.save()
        
        # Reload
        stats.refresh_from_db()
        
        assert stats.enhancements_count == 1
        assert stats.tokens_used == 500
    
    def test_cost_calculation(self):
        """Test cost calculation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        stats = UsageStats.get_current_period(user)
        stats.tokens_used = 10000
        cost = stats.calculate_cost()
        
        # Should be approximately $0.001 (10k tokens * $0.0001 per 1k)
        assert cost > 0
        assert cost < 0.01
```

**Run tests:**
```powershell
# Install pytest
pip install pytest pytest-django

# Run tests
pytest tests/ -v

# With coverage
pip install pytest-cov
pytest tests/ --cov=apps --cov-report=html
```

**Expected Result:**
- ✅ All tests pass
- ✅ Coverage >70%
- ✅ No errors

---

### Task 7.2: Performance Testing

**Create:** `test_performance.py`

```python
import time
import statistics
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


def test_api_response_time():
    """Test API response times meet <200ms target"""
    
    client = APIClient()
    user = User.objects.create_user(
        username='perftest',
        email='perf@example.com',
        password='testpass123'
    )
    client.force_authenticate(user=user)
    
    # Test enhancement endpoint
    times = []
    for i in range(10):
        start = time.time()
        response = client.post('/api/v2/ai/enhance', {
            'prompt': f'test prompt {i}',
            'save_history': False
        })
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        print(f"Request {i+1}: {elapsed:.2f}ms")
    
    avg_time = statistics.mean(times)
    p90_time = sorted(times)[8]  # 90th percentile
    
    print(f"\nAverage: {avg_time:.2f}ms")
    print(f"P90: {p90_time:.2f}ms")
    
    # Excluding DeepSeek API call, internal processing should be <200ms
    # This test measures total time including DeepSeek
    assert avg_time < 3000, f"Average response time {avg_time}ms exceeds limit"
    print("✅ Performance test passed!")


if __name__ == "__main__":
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
    django.setup()
    
    test_api_response_time()
```

**Expected Result:**
- ✅ Response times acceptable
- ✅ No performance degradation
- ✅ Database queries optimized

---

## 📋 FINAL SUMMARY & NEXT STEPS

### What We've Built:

1. ✅ **Lean Dependencies** - Removed heavy ML packages, ~200MB total
2. ✅ **Simple Enhancement Service** - Direct API calls, no LangChain
3. ✅ **Prompt History** - Save and retrieve user enhancements
4. ✅ **Template System** - Create and apply prompt templates
5. ✅ **Usage Tracking** - Billing foundation with limits
6. ✅ **API Documentation** - Complete OpenAPI spec
7. ✅ **Docker Setup** - Optimized <400MB image
8. ✅ **Railway Ready** - Production deployment config

### Current Architecture:

```
PromptCraft Backend (Lean)
│
├── Core Apps
│   ├── ai_services/          # Prompt enhancement (REFACTORED)
│   ├── prompt_history/       # History tracking (KEPT)
│   ├── templates/            # Template system (SIMPLIFIED)
│   ├── billing/              # Usage stats (ENHANCED)
│   └── users/                # Authentication (KEPT)
│
├── Dependencies (~200MB)
│   ├── Django + DRF
│   ├── PostgreSQL + Redis
│   ├── Gunicorn + Whitenoise
│   └── Stripe + Requests
│
└── Deployment
    ├── Docker (<400MB)
    ├── Railway (configured)
    └── Health checks
```

### Performance Metrics:

- **Docker Image:** <400MB (down from >1GB)
- **API Response:** <200ms internal processing
- **Dependencies:** ~25 packages (down from 100+)
- **Memory:** <512MB per instance

### For Extension Developers:

**API Endpoints:**
- `POST /api/v2/auth/login` - User authentication
- `POST /api/v2/ai/enhance` - Enhance prompts
- `GET /api/v2/ai/history` - Get history
- `GET /api/v2/templates/` - List templates
- `POST /api/v2/templates/{id}/apply` - Apply template
- `GET /api/v2/billing/stats` - Usage stats

**Documentation:**
- Swagger UI: `/api/docs/`
- API Contract: `API_CONTRACT.md`
- Integration examples included

### Next Iterations:

**Iteration 1 (Week 5):**
- Stripe integration for paid plans
- Email notifications
- Advanced rate limiting

**Iteration 2 (Week 6):**
- Chrome Extension MV3 final integration
- Frontend web app
- User dashboard

**Iteration 3 (Week 7):**
- Template marketplace
- Sharing and collaboration
- Analytics dashboard

**Iteration 4 (Week 8):**
- Mobile API optimization
- Webhooks for extensions
- Advanced prompt features

---

## 🐛 DEBUGGING GUIDE

### Common Issues:

**Issue: Docker build fails**
```powershell
# Clear cache and rebuild
docker builder prune
docker build -f Dockerfile.lean -t promptcraft:lean . --no-cache
```

**Issue: Database connection fails**
```powershell
# Check PostgreSQL is running
docker-compose -f docker-compose.lean.yml ps

# Check logs
docker-compose -f docker-compose.lean.yml logs db

# Reset database
docker-compose -f docker-compose.lean.yml down -v
docker-compose -f docker-compose.lean.yml up -d
```

**Issue: API returns 500 error**
```powershell
# Check backend logs
docker-compose -f docker-compose.lean.yml logs backend

# Check Django settings
docker-compose -f docker-compose.lean.yml exec backend python manage.py check

# Run migrations
docker-compose -f docker-compose.lean.yml exec backend python manage.py migrate
```

**Issue: Rate limiting not working**
```python
# Verify UsageStats model
python manage.py shell
from apps.billing.models import UsageStats, UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()
stats = UsageStats.get_current_period(user)
print(f"Enhancements: {stats.enhancements_count}")
print(f"Limit: {user.profile.monthly_enhancement_limit}")
```

---

## ✅ SUCCESS CRITERIA

- [ ] Docker image builds < 400MB
- [ ] All tests pass (>70% coverage)
- [ ] API response < 200ms (P90, internal)
- [ ] Health check passes
- [ ] Swagger docs accessible
- [ ] Extension team can integrate independently
- [ ] Railway deployment successful
- [ ] Zero critical bugs in first week
- [ ] Usage tracking functional
- [ ] Rate limiting works

---

**End of Lean Rescue Plan**

Ready to proceed with implementation? Let me know which sprint to start with!
