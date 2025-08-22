import openai
import anthropic
from django.conf import settings
from .models import AIInsight, AIInteraction
from .services_new import AnalyticsService
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

class AnalyticsService:
    """
    Analytics Service for tracking user behavior and generating insights
    
    Placeholder implementation until full analytics integration
    """
    
    @staticmethod
    def track_event(user, event_name, category, properties=None):
        """Track user events"""
        # For now, just print to console for debugging
        print(f"📊 Analytics: {event_name} for user {user.username} in category {category}")
        if properties:
            print(f"   Properties: {properties}")
        return True
    
    @staticmethod
    def get_user_insights(user):
        """Get user analytics insights"""
        return {
            'total_events': 0,
            'last_activity': None,
            'most_used_features': []
        }
    
    @staticmethod
    def track_template_usage(template, user, action):
        """Track template-specific usage"""
        print(f"📊 Template Analytics: {action} on '{template.title}' by {user.username}")
        return True
    
    @staticmethod
    def get_template_analytics(template):
        """Get analytics for a specific template"""
        return {
            'total_views': template.usage_count or 0,
            'completion_rate': template.completion_rate or 0,
            'average_rating': template.average_rating or 0,
            'user_feedback': []
        }