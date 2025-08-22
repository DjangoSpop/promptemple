"""
Professional Template Service Layer

This module provides high-level business logic for template operations,
abstracting database interactions and providing a clean API for template management.

Author: GitHub Copilot
Date: August 9, 2025
"""

from typing import List, Optional, Dict, Any, Tuple
from django.db.models import QuerySet, Q, Count, Avg, F
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import logging
import uuid

from apps.templates.models import (
    Template, TemplateCategory, PromptField, TemplateField, 
    TemplateUsage, TemplateRating, TemplateBookmark
)

User = get_user_model()
logger = logging.getLogger(__name__)

class TemplateServiceError(Exception):
    """Custom exception for template service errors"""
    pass

class TemplateService:
    """
    Professional service layer for template operations.
    
    This service provides high-level business logic for:
    - Template CRUD operations
    - Template search and filtering
    - Template analytics
    - Template usage tracking
    - Template recommendations
    """
    
    @staticmethod
    def get_public_templates(
        category_id: Optional[int] = None,
        search_query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        order_by: str = '-popularity_score',
        limit: Optional[int] = None
    ) -> QuerySet[Template]:
        """
        Get public templates with optional filtering.
        
        Args:
            category_id: Filter by category ID
            search_query: Search in title and description
            tags: Filter by tags
            order_by: Ordering field
            limit: Maximum number of results
            
        Returns:
            QuerySet of templates
        """
        try:
            queryset = Template.objects.filter(
                is_active=True,
                is_public=True
            ).select_related('author', 'category').prefetch_related('fields')
            
            # Category filter
            if category_id:
                queryset = queryset.filter(category_id=category_id)
            
            # Search filter
            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(tags__contains=[search_query])
                )
            
            # Tags filter
            if tags:
                for tag in tags:
                    queryset = queryset.filter(tags__contains=[tag])
            
            # Ordering
            queryset = queryset.order_by(order_by)
            
            # Limit
            if limit:
                queryset = queryset[:limit]
            
            logger.info(f"Retrieved {queryset.count()} public templates")
            return queryset
            
        except Exception as e:
            logger.error(f"Error retrieving public templates: {e}")
            raise TemplateServiceError(f"Failed to retrieve templates: {e}")
    
    @staticmethod
    def get_template_by_id(template_id: str, user: Optional[User] = None) -> Optional[Template]:
        """
        Get a template by ID with proper permission checking.
        
        Args:
            template_id: Template UUID
            user: Requesting user (optional)
            
        Returns:
            Template instance or None
        """
        try:
            template = Template.objects.select_related(
                'author', 'category'
            ).prefetch_related('fields').filter(
                id=template_id,
                is_active=True
            ).first()
            
            if not template:
                return None
            
            # Permission check
            if not template.is_public:
                if not user or (template.author != user and not user.is_staff):
                    logger.warning(f"Unauthorized access attempt to template {template_id}")
                    return None
            
            logger.info(f"Retrieved template {template_id} for user {user}")
            return template
            
        except Exception as e:
            logger.error(f"Error retrieving template {template_id}: {e}")
            raise TemplateServiceError(f"Failed to retrieve template: {e}")
    
    @staticmethod
    def get_trending_templates(limit: int = 10, days: int = 7) -> QuerySet[Template]:
        """
        Get trending templates based on recent activity.
        
        Args:
            limit: Maximum number of templates
            days: Number of days to consider for trending
            
        Returns:
            QuerySet of trending templates
        """
        try:
            from datetime import timedelta
            cutoff_date = timezone.now() - timedelta(days=days)
            
            trending = Template.objects.filter(
                is_active=True,
                is_public=True
            ).annotate(
                recent_usage=Count(
                    'usage_logs',
                    filter=Q(usage_logs__started_at__gte=cutoff_date)
                ),
                recent_ratings=Count(
                    'ratings',
                    filter=Q(ratings__created_at__gte=cutoff_date)
                )
            ).order_by(
                '-recent_usage', '-recent_ratings', '-popularity_score'
            )[:limit]
            
            logger.info(f"Retrieved {trending.count()} trending templates")
            return trending
            
        except Exception as e:
            logger.error(f"Error retrieving trending templates: {e}")
            raise TemplateServiceError(f"Failed to retrieve trending templates: {e}")
    
    @staticmethod
    def get_featured_templates(limit: int = 5) -> QuerySet[Template]:
        """
        Get featured templates.
        
        Args:
            limit: Maximum number of templates
            
        Returns:
            QuerySet of featured templates
        """
        try:
            featured = Template.objects.filter(
                is_active=True,
                is_public=True,
                is_featured=True
            ).order_by('-created_at')[:limit]
            
            logger.info(f"Retrieved {featured.count()} featured templates")
            return featured
            
        except Exception as e:
            logger.error(f"Error retrieving featured templates: {e}")
            raise TemplateServiceError(f"Failed to retrieve featured templates: {e}")
    
    @staticmethod
    @transaction.atomic
    def create_template(
        user: User,
        title: str,
        description: str,
        category_id: int,
        template_content: str,
        fields_data: List[Dict[str, Any]],
        **kwargs
    ) -> Template:
        """
        Create a new template with fields.
        
        Args:
            user: Template author
            title: Template title
            description: Template description
            category_id: Category ID
            template_content: Template content with placeholders
            fields_data: List of field definitions
            **kwargs: Additional template attributes
            
        Returns:
            Created template instance
        """
        try:
            # Validate category
            try:
                category = TemplateCategory.objects.get(id=category_id, is_active=True)
            except TemplateCategory.DoesNotExist:
                raise TemplateServiceError(f"Category {category_id} not found")
            
            # Create template
            template = Template.objects.create(
                id=uuid.uuid4(),
                title=title,
                description=description,
                category=category,
                template_content=template_content,
                author=user,
                version=kwargs.get('version', '1.0.0'),
                tags=kwargs.get('tags', []),
                is_public=kwargs.get('is_public', False),
                is_active=True
            )
            
            # Create fields
            for order, field_data in enumerate(fields_data):
                field = PromptField.objects.create(
                    id=uuid.uuid4(),
                    label=field_data['label'],
                    placeholder=field_data.get('placeholder', ''),
                    field_type=field_data.get('field_type', 'text'),
                    is_required=field_data.get('is_required', False),
                    default_value=field_data.get('default_value', ''),
                    validation_pattern=field_data.get('validation_pattern', ''),
                    help_text=field_data.get('help_text', ''),
                    options=field_data.get('options', []),
                    order=order
                )
                
                TemplateField.objects.create(
                    template=template,
                    field=field,
                    order=order
                )
            
            logger.info(f"Created template {template.id} by user {user.id}")
            return template
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise TemplateServiceError(f"Failed to create template: {e}")
    
    @staticmethod
    def start_template_usage(user: User, template_id: str, **kwargs) -> TemplateUsage:
        """
        Start a template usage session.
        
        Args:
            user: User starting the template
            template_id: Template UUID
            **kwargs: Additional usage data
            
        Returns:
            TemplateUsage instance
        """
        try:
            template = Template.objects.get(id=template_id, is_active=True)
            
            # Create usage session
            usage = TemplateUsage.objects.create(
                id=uuid.uuid4(),
                template=template,
                user=user,
                device_type=kwargs.get('device_type', ''),
                app_version=kwargs.get('app_version', ''),
                referrer_source=kwargs.get('referrer_source', '')
            )
            
            # Update template usage count
            Template.objects.filter(id=template_id).update(
                usage_count=F('usage_count') + 1
            )
            
            logger.info(f"Started usage session {usage.id} for template {template_id}")
            return usage
            
        except Template.DoesNotExist:
            raise TemplateServiceError(f"Template {template_id} not found")
        except Exception as e:
            logger.error(f"Error starting template usage: {e}")
            raise TemplateServiceError(f"Failed to start template usage: {e}")
    
    @staticmethod
    def complete_template_usage(
        usage_id: str,
        time_spent_seconds: Optional[int] = None,
        generated_prompt_length: Optional[int] = None,
        field_completion_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete a template usage session.
        
        Args:
            usage_id: Usage session UUID
            time_spent_seconds: Time spent on template
            generated_prompt_length: Length of generated prompt
            field_completion_data: Field completion data
            
        Returns:
            Completion results with rewards
        """
        try:
            usage = TemplateUsage.objects.get(
                id=usage_id,
                was_completed=False
            )
            
            # Mark as completed
            usage.was_completed = True
            usage.completed_at = timezone.now()
            usage.time_spent_seconds = time_spent_seconds
            usage.generated_prompt_length = generated_prompt_length
            usage.field_completion_data = field_completion_data or {}
            usage.save()
            
            # Update template completion rate
            template = usage.template
            total_usages = template.usage_logs.count()
            completed_usages = template.usage_logs.filter(was_completed=True).count()
            
            if total_usages > 0:
                template.completion_rate = completed_usages / total_usages
                template.save(update_fields=['completion_rate'])
            
            # Calculate rewards (basic implementation)
            base_points = 10
            time_bonus = 5 if time_spent_seconds and time_spent_seconds < 300 else 0
            length_bonus = 5 if generated_prompt_length and generated_prompt_length > 100 else 0
            
            total_points = base_points + time_bonus + length_bonus
            
            logger.info(f"Completed usage session {usage_id} with {total_points} points")
            
            return {
                'points_earned': total_points,
                'time_bonus': time_bonus,
                'length_bonus': length_bonus,
                'completion_time': usage.completed_at
            }
            
        except TemplateUsage.DoesNotExist:
            raise TemplateServiceError(f"Usage session {usage_id} not found")
        except Exception as e:
            logger.error(f"Error completing template usage: {e}")
            raise TemplateServiceError(f"Failed to complete template usage: {e}")
    
    @staticmethod
    def get_template_analytics(template_id: str, user: User) -> Dict[str, Any]:
        """
        Get analytics for a template (owner only).
        
        Args:
            template_id: Template UUID
            user: Requesting user
            
        Returns:
            Analytics data
        """
        try:
            template = Template.objects.get(id=template_id)
            
            # Permission check
            if template.author != user and not user.is_staff:
                raise TemplateServiceError("Permission denied")
            
            # Calculate analytics
            total_usage = template.usage_logs.count()
            completed_usage = template.usage_logs.filter(was_completed=True).count()
            unique_users = template.usage_logs.values('user').distinct().count()
            avg_rating = template.ratings.aggregate(avg=Avg('rating'))['avg'] or 0
            total_ratings = template.ratings.count()
            
            # Time-based analytics
            from datetime import timedelta
            week_ago = timezone.now() - timedelta(days=7)
            recent_usage = template.usage_logs.filter(started_at__gte=week_ago).count()
            
            analytics = {
                'template_id': str(template_id),
                'total_usage': total_usage,
                'completed_usage': completed_usage,
                'completion_rate': template.completion_rate,
                'unique_users': unique_users,
                'average_rating': round(avg_rating, 2),
                'total_ratings': total_ratings,
                'recent_usage_7d': recent_usage,
                'popularity_score': template.popularity_score,
                'created_at': template.created_at,
                'updated_at': template.updated_at
            }
            
            logger.info(f"Generated analytics for template {template_id}")
            return analytics
            
        except Template.DoesNotExist:
            raise TemplateServiceError(f"Template {template_id} not found")
        except Exception as e:
            logger.error(f"Error generating template analytics: {e}")
            raise TemplateServiceError(f"Failed to generate analytics: {e}")
    
    @staticmethod
    def get_user_recommendations(user: User, limit: int = 10) -> List[Template]:
        """
        Get personalized template recommendations for a user.
        
        Args:
            user: User to generate recommendations for
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended templates
        """
        try:
            # Get user's usage history
            used_templates = TemplateUsage.objects.filter(
                user=user
            ).values_list('template_id', flat=True)
            
            # Get user's preferred categories
            preferred_categories = TemplateUsage.objects.filter(
                user=user
            ).values('template__category').annotate(
                usage_count=Count('id')
            ).order_by('-usage_count')[:3]
            
            category_ids = [cat['template__category'] for cat in preferred_categories]
            
            # Recommend templates from preferred categories that user hasn't used
            recommendations = Template.objects.filter(
                is_active=True,
                is_public=True,
                category_id__in=category_ids
            ).exclude(
                id__in=used_templates
            ).order_by(
                '-popularity_score', '-average_rating'
            )[:limit]
            
            # If not enough recommendations, add popular templates
            if recommendations.count() < limit:
                additional = Template.objects.filter(
                    is_active=True,
                    is_public=True
                ).exclude(
                    id__in=used_templates
                ).exclude(
                    id__in=[t.id for t in recommendations]
                ).order_by('-popularity_score')[:limit - recommendations.count()]
                
                recommendations = list(recommendations) + list(additional)
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {user.id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating user recommendations: {e}")
            raise TemplateServiceError(f"Failed to generate recommendations: {e}")

class CategoryService:
    """Service layer for template categories"""
    
    @staticmethod
    def get_active_categories() -> QuerySet[TemplateCategory]:
        """Get all active categories with template counts"""
        try:
            categories = TemplateCategory.objects.filter(
                is_active=True
            ).annotate(
                template_count=Count(
                    'templates', 
                    filter=Q(templates__is_active=True, templates__is_public=True)
                )
            ).order_by('order', 'name')
            
            logger.info(f"Retrieved {categories.count()} active categories")
            return categories
            
        except Exception as e:
            logger.error(f"Error retrieving categories: {e}")
            raise TemplateServiceError(f"Failed to retrieve categories: {e}")
    
    @staticmethod
    def get_category_templates(category_id: int, **kwargs) -> QuerySet[Template]:
        """Get templates in a specific category"""
        try:
            category = TemplateCategory.objects.get(id=category_id, is_active=True)
            
            templates = Template.objects.filter(
                category=category,
                is_active=True,
                is_public=True
            ).select_related('author').order_by(
                kwargs.get('order_by', '-popularity_score')
            )
            
            limit = kwargs.get('limit')
            if limit:
                templates = templates[:limit]
            
            logger.info(f"Retrieved {templates.count()} templates for category {category_id}")
            return templates
            
        except TemplateCategory.DoesNotExist:
            raise TemplateServiceError(f"Category {category_id} not found")
        except Exception as e:
            logger.error(f"Error retrieving category templates: {e}")
            raise TemplateServiceError(f"Failed to retrieve category templates: {e}")
