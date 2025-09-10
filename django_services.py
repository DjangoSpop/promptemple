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
