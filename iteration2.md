# apps/ai_services/services.py - Enhanced AI Services
import openai
import anthropic
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import (
    AIProvider, AIModel, AIInteraction, AIInsight, 
    PersonalizedRecommendation, AIUsageQuota, AIPromptTemplate,
    MLModelPrediction
)
from apps.analytics.services import AnalyticsService
from apps.gamification.services import GamificationService
import time
import logging
import json
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class AIService:
    """Enhanced AI service with multiple providers and advanced features"""
    
    @classmethod
    def get_available_providers(cls) -> List[AIProvider]:
        """Get all active AI providers"""
        return AIProvider.objects.filter(is_active=True)
    
    @classmethod
    def get_best_model_for_task(cls, task_type: str, user=None) -> Optional[AIModel]:
        """Select the best AI model for a specific task"""
        # Priority: user preference > task optimization > default
        models = AIModel.objects.filter(
            is_active=True,
            provider__is_active=True
        ).select_related('provider')
        
        # Task-specific optimization
        if task_type == 'template_analysis':
            models = models.filter(provider__supports_text_analysis=True)
        elif task_type == 'content_generation':
            models = models.filter(provider__supports_content_generation=True)
        elif task_type == 'optimization':
            models = models.filter(provider__supports_optimization=True)
        
        # Return highest quality model
        return models.order_by('-quality_score', '-is_default').first()
    
    @classmethod
    def check_user_quota(cls, user, estimated_tokens: int = 1000) -> bool:
        """Check if user can make AI request"""
        quota, created = AIUsageQuota.objects.get_or_create(
            user=user,
            defaults={
                'monthly_requests_limit': 100,
                'daily_requests_limit': 20,
                'monthly_tokens_limit': 50000,
                'daily_tokens_limit': 5000,
            }
        )
        
        # Reset quotas if needed
        today = timezone.now().date()
        if quota.last_daily_reset < today:
            quota.daily_requests_used = 0
            quota.daily_tokens_used = 0
            quota.last_daily_reset = today
        
        current_month = timezone.now().date().replace(day=1)
        if quota.last_monthly_reset < current_month:
            quota.monthly_requests_used = 0
            quota.monthly_tokens_used = 0
            quota.last_monthly_reset = current_month
        
        quota.save()
        
        return quota.can_make_request(estimated_tokens)
    
    @classmethod
    def analyze_template(cls, template, user, analysis_type: str = 'comprehensive') -> Dict[str, Any]:
        """Analyze template with AI for optimization suggestions"""
        if not cls.check_user_quota(user):
            return {
                'error': 'AI quota exceeded',
                'message': 'You have reached your daily AI usage limit. Upgrade to premium for unlimited access.',
                'quota_info': cls._get_quota_info(user)
            }
        
        ai_model = cls.get_best_model_for_task('template_analysis', user)
        if not ai_model:
            return {'error': 'No AI model available'}
        
        start_time = time.time()
        
        try:
            # Build analysis prompt
            prompt = cls._build_template_analysis_prompt(template, analysis_type)
            
            # Make AI request
            response_data = cls._make_ai_request(ai_model, prompt, user)
            
            response_time = int((time.time() - start_time) * 1000)
            
            # Record successful interaction
            interaction = AIInteraction.objects.create(
                user=user,
                ai_model=ai_model,
                interaction_type='template_analysis',
                request_prompt=prompt,
                request_metadata={'analysis_type': analysis_type},
                response_content=response_data.get('content', ''),
                response_metadata=response_data.get('metadata', {}),
                tokens_input=response_data.get('tokens_input', 0),
                tokens_output=response_data.get('tokens_output', 0),
                response_time_ms=response_time,
                was_successful=True,
                confidence_score=response_data.get('confidence', 0.8),
                related_template=template,
                estimated_cost=response_data.get('cost', 0)
            )
            
            # Update user quota
            cls._update_user_quota(user, interaction.total_tokens)
            
            # Generate insights
            insights = cls._extract_insights_from_response(
                response_data['content'], template, user, interaction
            )
            
            # Track analytics
            AnalyticsService.track_event(
                user=user,
                event_name='ai_template_analysis',
                category='ai_usage',
                properties={
                    'template_id': str(template.id),
                    'analysis_type': analysis_type,
                    'response_time_ms': response_time,
                    'tokens_used': interaction.total_tokens,
                    'insights_count': len(insights)
                }
            )
            
            # Award credits for AI usage
            GamificationService.update_daily_challenge_progress(
                user, 'use_ai_assistant', 1
            )
            
            return {
                'interaction_id': interaction.id,
                'insights': insights,
                'analysis_summary': response_data.get('summary', ''),
                'confidence': response_data.get('confidence', 0.8),
                'processing_time_ms': response_time,
                'tokens_used': interaction.total_tokens,
                'remaining_quota': cls._get_quota_info(user)
            }
            
        except Exception as e:
            logger.error(f"AI template analysis failed: {e}")
            
            # Record failed interaction
            AIInteraction.objects.create(
                user=user,
                ai_model=ai_model,
                interaction_type='template_analysis',
                request_prompt=prompt,
                response_time_ms=int((time.time() - start_time) * 1000),
                was_successful=False,
                error_message=str(e),
                related_template=template
            )
            
            return {
                'error': 'AI analysis failed',
                'message': 'We encountered an issue analyzing your template. Please try again.',
                'retry_available': True
            }
    
    @classmethod
    def generate_template_suggestions(cls, user, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate personalized template recommendations using AI"""
        if not cls.check_user_quota(user, 500):  # Lower token estimate for suggestions
            return []
        
        ai_model = cls.get_best_model_for_task('content_generation', user)
        if not ai_model:
            return []
        
        # Analyze user behavior for personalization
        user_data = cls._get_user_behavior_data(user)
        
        # Build suggestion prompt
        prompt = cls._build_suggestion_prompt(user_data, context)
        
        try:
            response_data = cls._make_ai_request(ai_model, prompt, user)
            
            # Parse suggestions
            suggestions = cls._parse_template_suggestions(response_data['content'])
            
            # Store recommendations
            recommendations = []
            for suggestion in suggestions:
                if suggestion.get('template_id'):  # If suggesting existing template
                    try:
                        from apps.templates.models import Template
                        template = Template.objects.get(id=suggestion['template_id'])
                        
                        recommendation = PersonalizedRecommendation.objects.create(
                            user=user,
                            template=template,
                            confidence=suggestion.get('confidence', 0.7),
                            relevance_score=suggestion.get('relevance', 0.8),
                            popularity_factor=template.popularity_score / 100,
                            reasoning=suggestion.get('reasoning', ''),
                            recommendation_factors=suggestion.get('factors', []),
                            estimated_completion_time=suggestion.get('time_estimate', 15),
                            predicted_success_rate=suggestion.get('success_rate', 0.8),
                            difficulty_level=suggestion.get('difficulty', 'intermediate'),
                            recommendation_context=context.get('context', 'daily_use'),
                            expires_at=timezone.now() + timezone.timedelta(days=7)
                        )
                        
                        recommendations.append({
                            'id': recommendation.id,
                            'template': {
                                'id': template.id,
                                'title': template.title,
                                'description': template.description,
                                'category': template.category.name,
                            },
                            'confidence': recommendation.confidence,
                            'reasoning': recommendation.reasoning,
                            'estimated_time': recommendation.estimated_completion_time,
                            'difficulty': recommendation.difficulty_level
                        })
                    except Template.DoesNotExist:
                        continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"AI suggestion generation failed: {e}")
            return []
    
    @classmethod
    def enhance_prompt_content(cls, content: str, user, enhancement_type: str = 'clarity') -> Dict[str, Any]:
        """Enhance prompt content using AI"""
        if not cls.check_user_quota(user):
            return {'error': 'AI quota exceeded'}
        
        ai_model = cls.get_best_model_for_task('optimization', user)
        if not ai_model:
            return {'error': 'No AI model available'}
        
        # Build enhancement prompt
        prompt = cls._build_enhancement_prompt(content, enhancement_type)
        
        try:
            response_data = cls._make_ai_request(ai_model, prompt, user)
            
            # Record interaction
            interaction = AIInteraction.objects.create(
                user=user,
                ai_model=ai_model,
                interaction_type='prompt_enhancement',
                request_prompt=prompt,
                request_metadata={'enhancement_type': enhancement_type},
                response_content=response_data.get('content', ''),
                tokens_input=response_data.get('tokens_input', 0),
                tokens_output=response_data.get('tokens_output', 0),
                was_successful=True,
                confidence_score=response_data.get('confidence', 0.8)
            )
            
            cls._update_user_quota(user, interaction.total_tokens)
            
            return {
                'enhanced_content': response_data.get('enhanced_content', ''),
                'improvements': response_data.get('improvements', []),
                'confidence': response_data.get('confidence', 0.8),
                'original_length': len(content),
                'enhanced_length': len(response_data.get('enhanced_content', '')),
                'interaction_id': interaction.id
            }
            
        except Exception as e:
            logger.error(f"AI content enhancement failed: {e}")
            return {'error': 'Enhancement failed', 'message': str(e)}
    
    # Private helper methods
    @classmethod
    def _make_ai_request(cls, ai_model: AIModel, prompt: str, user) -> Dict[str, Any]:
        """Make request to AI provider"""
        provider = ai_model.provider
        
        if provider.name == 'openai':
            return cls._make_openai_request(ai_model, prompt)
        elif provider.name == 'anthropic':
            return cls._make_anthropic_request(ai_model, prompt)
        else:
            raise ValueError(f"Unsupported AI provider: {provider.name}")
    
    @classmethod
    def _make_openai_request(cls, ai_model: AIModel, prompt: str) -> Dict[str, Any]:
        """Make request to OpenAI API"""
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=ai_model.name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=min(ai_model.max_context_length // 2, 2000),
            temperature=0.3
        )
        
        return {
            'content': response.choices[0].message.content,
            'tokens_input': response.usage.prompt_tokens,
            'tokens_output': response.usage.completion_tokens,
            'cost': cls._calculate_openai_cost(ai_model, response.usage),
            'confidence': 0.8,
            'metadata': {
                'model': ai_model.name,
                'finish_reason': response.choices[0].finish_reason
            }
        }
    
    @classmethod
    def _make_anthropic_request(cls, ai_model: AIModel, prompt: str) -> Dict[str, Any]:
        """Make request to Anthropic API"""
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        response = client.messages.create(
            model=ai_model.name,
            max_tokens=min(ai_model.max_context_length // 2, 2000),
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'content': response.content[0].text,
            'tokens_input': response.usage.input_tokens,
            'tokens_output': response.usage.output_tokens,
            'cost': cls._calculate_anthropic_cost(ai_model, response.usage),
            'confidence': 0.8,
            'metadata': {
                'model': ai_model.name,
                'stop_reason': response.stop_reason
            }
        }
    
    @classmethod
    def _calculate_openai_cost(cls, ai_model: AIModel, usage) -> float:
        """Calculate OpenAI request cost"""
        input_cost = usage.prompt_tokens * float(ai_model.cost_per_input_token)
        output_cost = usage.completion_tokens * float(ai_model.cost_per_output_token)
        return input_cost + output_cost
    
    @classmethod
    def _calculate_anthropic_cost(cls, ai_model: AIModel, usage) -> float:
        """Calculate Anthropic request cost"""
        input_cost = usage.input_tokens * float(ai_model.cost_per_input_token)
        output_cost = usage.output_tokens * float(ai_model.cost_per_output_token)
        return input_cost + output_cost
    
    @classmethod
    def _build_template_analysis_prompt(cls, template, analysis_type: str) -> str:
        """Build AI prompt for template analysis"""
        base_prompt = f"""
        Analyze this prompt template for optimization opportunities:
        
        Title: {template.title}
        Description: {template.description}
        Category: {template.category.name}
        Content: {template.template_content}
        
        Fields ({len(template.fields.all())} total):
        """
        
        for field in template.fields.all():
            base_prompt += f"\n- {field.label} ({field.field_type}): {field.placeholder}"
            if field.is_required:
                base_prompt += " [Required]"
        
        if analysis_type == 'comprehensive':
            base_prompt += """
            
            Please provide a comprehensive analysis including:
            1. Clarity and readability assessment
            2. Structure and organization review
            3. Field optimization suggestions
            4. User experience improvements
            5. AI interaction effectiveness
            6. Overall quality score (1-10)
            
            Format your response as JSON with these sections:
            {
                "overall_score": 8.5,
                "clarity_score": 9,
                "structure_score": 8,
                "suggestions": [
                    {"type": "improvement", "field": "template_content", "suggestion": "...", "priority": "high"},
                    {"type": "field_optimization", "field": "field_name", "suggestion": "...", "priority": "medium"}
                ],
                "strengths": ["list", "of", "strengths"],
                "areas_for_improvement": ["list", "of", "improvements"],
                "recommended_actions": ["action1", "action2"]
            }
            """
        elif analysis_type == 'quick':
            base_prompt += """
            
            Provide a quick analysis focusing on:
            1. Top 3 improvement opportunities
            2. Overall quality score (1-10)
            3. Quick wins for better user experience
            
            Keep response concise and actionable.
            """
        
        return base_prompt
    
    @classmethod
    def _build_suggestion_prompt(cls, user_data: Dict, context: Dict) -> str:
        """Build AI prompt for personalized suggestions"""
        return f"""
        Generate personalized template recommendations for this user:
        
        User Profile:
        - Level: {user_data.get('level', 1)}
        - Templates Created: {user_data.get('templates_created', 0)}
        - Preferred Categories: {user_data.get('preferred_categories', [])}
        - Recent Activity: {user_data.get('recent_activity', [])}
        - Skill Level: {user_data.get('skill_level', 'beginner')}
        
        Context:
        - Current Focus: {context.get('focus_area', 'general')}
        - Time Available: {context.get('time_available', '15-30 minutes')}
        - Goal: {context.get('goal', 'skill_improvement')}
        
        Suggest 3-5 templates that would be valuable for this user.
        Consider their experience level, interests, and current goals.
        
        Return as JSON array:
        [
            {
                "template_id": "existing_template_id_or_null",
                "title": "Suggested Template Title",
                "description": "Why this template is recommended",
                "confidence": 0.85,
                "relevance": 0.9,
                "reasoning": "Detailed explanation of why this fits the user",
                "factors": ["factor1", "factor2", "factor3"],
                "time_estimate": 20,
                "success_rate": 0.8,
                "difficulty": "intermediate"
            }
        ]
        """
    
    @classmethod
    def _build_enhancement_prompt(cls, content: str, enhancement_type: str) -> str:
        """Build AI prompt for content enhancement"""
        enhancements = {
            'clarity': 'Make the content clearer and easier to understand',
            'structure': 'Improve the organization and flow of the content',
            'engagement': 'Make the content more engaging and compelling',
            'conciseness': 'Make the con