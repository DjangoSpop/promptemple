from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, F
from django.utils import timezone
from django.db import transaction
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.core.cache import cache
import time
import logging

from .models import (
    Template, TemplateCategory, PromptLibrary, UserIntent, 
    ChatMessage, PerformanceMetrics
)
from .serializers import (
    TemplateListSerializer, TemplateDetailSerializer, 
    TemplateCreateUpdateSerializer, TemplateCategorySerializer,
    TemplateUsageSerializer, TemplateRatingSerializer,
    TemplateAnalyticsSerializer
)
from apps.analytics.services import AnalyticsService
from apps.ai_services.services import AIService
from apps.gamification.services import GamificationService

# Set up logger first
logger = logging.getLogger(__name__)

# Import new high-performance services
try:
    from .search_services import search_service
    from .cache_services import multi_cache, performance_monitor
    from .langchain_services import langchain_service
    logger.info("High-performance services loaded successfully")
except ImportError as e:
    logger.warning(f"High-performance services not available: {e}")
    search_service = None
    multi_cache = None
    performance_monitor = None
    langchain_service = None


class TemplateCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for template categories
    
    Provides:
    - List all categories
    - Retrieve single category
    - Category statistics
    """
    
    queryset = TemplateCategory.objects.filter(is_active=True)
    serializer_class = TemplateCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'])
    def templates(self, request, pk=None):
        """Get templates in this category"""
        category = self.get_object()
        templates = Template.objects.filter(
            category=category,
            is_active=True,
            is_public=True
        ).select_related('author', 'category').order_by('-popularity_score')
        
        # Apply pagination
        page = self.paginate_queryset(templates)
        if page is not None:
            serializer = TemplateListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TemplateListSerializer(templates, many=True)
        return Response(serializer.data)


class TemplateViewSet(viewsets.ModelViewSet):
    """
    Complete CRUD ViewSet for templates
    
    Features:
    - List, create, retrieve, update, delete templates
    - Advanced filtering and search
    - Custom actions for usage tracking
    - AI integration
    - Analytics and ratings
    """
    
    queryset = Template.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'is_public', 'author']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = [
        'created_at', 'updated_at', 'popularity_score', 
        'usage_count', 'average_rating', 'title'
    ]
    ordering = ['-popularity_score', '-created_at']
    
    def get_queryset(self):
        """
        Customize queryset based on action and user permissions
        """
        queryset = Template.objects.filter(is_active=True)
        
        # Optimize database queries
        queryset = queryset.select_related('author', 'category').prefetch_related('fields')
        
        if self.action == 'list':
            # For list view, show public templates unless filtering by user
            if self.request.query_params.get('my_templates'):
                if self.request.user.is_authenticated:
                    queryset = queryset.filter(author=self.request.user)
                else:
                    queryset = queryset.none()
            else:
                queryset = queryset.filter(is_public=True)
        
        return queryset
    
    def get_serializer_class(self):
        """
        Choose appropriate serializer based on action
        """
        if self.action == 'list':
            return TemplateListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TemplateCreateUpdateSerializer
        return TemplateDetailSerializer
    
    def perform_create(self, serializer):
        """
        Handle template creation with additional logic
        """
        template = serializer.save(author=self.request.user)
        
        # Track analytics
        AnalyticsService.track_event(
            user=self.request.user,
            event_name='template_created',
            category='template',
            properties={
                'template_id': str(template.id),
                'title': template.title,
                'category': template.category.name,
                'field_count': template.field_count
            }
        )
        
        # Award experience points
        user = self.request.user
        user.experience_points += 25
        user.save(update_fields=['experience_points'])
        
        # Check for achievements
        GamificationService.check_achievements(user)
    
    def perform_update(self, serializer):
        """
        Handle template updates
        """
        template = serializer.save()
        
        # Track analytics
        AnalyticsService.track_event(
            user=self.request.user,
            event_name='template_updated',
            category='template',
            properties={
                'template_id': str(template.id),
                'title': template.title
            }
        )
    
    def perform_destroy(self, instance):
        """
        Soft delete template instead of hard delete
        """
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        
        # Track analytics
        AnalyticsService.track_event(
            user=self.request.user,
            event_name='template_deleted',
            category='template',
            properties={
                'template_id': str(instance.id),
                'title': instance.title
            }
        )
    
    @action(detail=True, methods=['post'])
    def start_usage(self, request, pk=None):
        """
        Start using a template - creates usage tracking record
        """
        template = self.get_object()
        
        # Check if user can afford credits (if required)
        if template.category.name in ['Premium', 'AI-Powered']:
            cost = 5  # Premium templates cost credits
            if not request.user.can_afford(cost):
                return Response(
                    {'error': 'Insufficient credits'}, 
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )
        
        # Create usage record
        usage = TemplateUsage.objects.create(
            template=template,
            user=request.user,
            device_type=request.data.get('device_type', ''),
            app_version=request.data.get('app_version', '')
        )
        
        # Update template usage count
        template.usage_count = F('usage_count') + 1
        template.save(update_fields=['usage_count'])
        
        # Spend credits if required
        if template.category.name in ['Premium', 'AI-Powered']:
            GamificationService.spend_credits(
                user=request.user,
                amount=cost,
                reason=f'Used premium template: {template.title}',
                transaction_type='spent_premium'
            )
        
        # Track analytics
        AnalyticsService.track_event(
            user=request.user,
            event_name='template_usage_started',
            category='template',
            properties={
                'template_id': str(template.id),
                'usage_id': str(usage.id),
                'device_type': usage.device_type
            }
        )
        
        return Response({
            'usage_id': str(usage.id),
            'message': 'Template usage started successfully',
            'remaining_credits': request.user.credits
        })
    
    @action(detail=True, methods=['post'])
    def complete_usage(self, request, pk=None):
        """
        Complete template usage and award rewards
        """
        template = self.get_object()
        usage_id = request.data.get('usage_id')
        
        if not usage_id:
            return Response(
                {'error': 'usage_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            usage = TemplateUsage.objects.get(
                id=usage_id,
                template=template,
                user=request.user,
                was_completed=False
            )
            
            # Mark as completed
            usage.was_completed = True
            usage.completed_at = timezone.now()
            usage.time_spent_seconds = request.data.get('time_spent_seconds')
            usage.generated_prompt_length = request.data.get('prompt_length')
            usage.field_completion_data = request.data.get('field_data', {})
            usage.save()
            
            # Update user stats
            user = request.user
            user.templates_completed += 1
            user.total_prompts_generated += 1
            user.save(update_fields=['templates_completed', 'total_prompts_generated'])
            
            # Award completion rewards
            base_credits = 10
            bonus_credits = 0
            
            # Time-based bonus
            if usage.time_spent_seconds and usage.time_spent_seconds < 300:  # Under 5 minutes
                bonus_credits += 5
            
            # Quality bonus based on prompt length
            if usage.generated_prompt_length and usage.generated_prompt_length > 100:
                bonus_credits += 5
            
            total_credits = base_credits + bonus_credits
            
            GamificationService.award_credits(
                user=user,
                amount=total_credits,
                reason=f'Completed template: {template.title}',
                transaction_type='earned_completion'
            )
            
            # Award experience points
            experience_points = 15 + (bonus_credits * 2)
            user.experience_points += experience_points
            user.save(update_fields=['experience_points'])
            
            # Update template completion rate
            total_usages = template.usage_logs.count()
            completed_usages = template.usage_logs.filter(was_completed=True).count()
            template.completion_rate = completed_usages / total_usages if total_usages > 0 else 0
            template.save(update_fields=['completion_rate'])
            
            # Check for achievements
            GamificationService.check_achievements(user)
            
            # Update daily challenge progress
            GamificationService.update_daily_challenge_progress(
                user=user,
                challenge_type='complete_templates',
                value=1
            )
            
            # Track analytics
            AnalyticsService.track_event(
                user=request.user,
                event_name='template_usage_completed',
                category='template',
                properties={
                    'template_id': str(template.id),
                    'usage_id': str(usage.id),
                    'time_spent': usage.time_spent_seconds,
                    'prompt_length': usage.generated_prompt_length,
                    'credits_earned': total_credits,
                    'experience_earned': experience_points
                }
            )
            
            return Response({
                'message': 'Template completed successfully',
                'rewards': {
                    'credits_earned': total_credits,
                    'experience_earned': experience_points,
                    'bonus_credits': bonus_credits
                },
                'user_stats': {
                    'total_credits': user.credits,
                    'level': user.level,
                    'experience_points': user.experience_points
                }
            })
            
        except TemplateUsage.DoesNotExist:
            return Response(
                {'error': 'Usage record not found or already completed'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def rate_template(self, request, pk=None):
        """
        Rate and review a template
        """
        template = self.get_object()
        
        # Validate user has used this template
        has_used = TemplateUsage.objects.filter(
            template=template,
            user=request.user,
            was_completed=True
        ).exists()
        
        if not has_used:
            return Response(
                {'error': 'You must complete this template before rating it'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TemplateRatingSerializer(data=request.data)
        if serializer.is_valid():
            # Update or create rating
            rating, created = TemplateRating.objects.update_or_create(
                template=template,
                user=request.user,
                defaults={
                    'rating': serializer.validated_data['rating'],
                    'review': serializer.validated_data.get('review', '')
                }
            )
            
            # Update template average rating
            avg_rating = template.ratings.aggregate(avg=Avg('rating'))['avg'] or 0
            template.average_rating = round(avg_rating, 2)
            
            # Update popularity score
            template.update_popularity_score()
            
            # Track analytics
            AnalyticsService.track_event(
                user=request.user,
                event_name='template_rated',
                category='template',
                properties={
                    'template_id': str(template.id),
                    'rating': rating.rating,
                    'has_review': bool(rating.review),
                    'is_new_rating': created
                }
            )
            
            return Response(TemplateRatingSerializer(rating).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        Get trending templates based on recent activity
        """
        # Calculate trending score based on recent usage
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        
        trending_templates = Template.objects.filter(
            is_active=True,
            is_public=True
        ).annotate(
            recent_usage=Count(
                'usage_logs',
                filter=Q(usage_logs__started_at__gte=week_ago)
            )
        ).order_by('-recent_usage', '-popularity_score')[:10]
        
        serializer = TemplateListSerializer(trending_templates, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured templates
        """
        featured_templates = Template.objects.filter(
            is_active=True,
            is_public=True,
            is_featured=True
        ).order_by('-created_at')[:5]
        
        serializer = TemplateListSerializer(featured_templates, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_templates(self, request):
        """
        Get current user's templates
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_templates = Template.objects.filter(
            author=request.user,
            is_active=True
        ).order_by('-created_at')
        
        # Apply pagination
        page = self.paginate_queryset(user_templates)
        if page is not None:
            serializer = TemplateListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TemplateListSerializer(user_templates, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def analyze_with_ai(self, request, pk=None):
        """
        Analyze template with AI for optimization suggestions
        """
        template = self.get_object()
        
        # Check if user has AI assistance enabled
        if not request.user.ai_assistance_enabled:
            return Response(
                {'error': 'AI assistance is disabled in your settings'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user can afford AI analysis
        ai_cost = 20
        if not request.user.can_afford(ai_cost):
            return Response(
                {'error': f'AI analysis costs {ai_cost} credits. You have {request.user.credits} credits.'}, 
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        
        try:
            # Spend credits for AI analysis
            GamificationService.spend_credits(
                user=request.user,
                amount=ai_cost,
                reason=f'AI analysis for template: {template.title}',
                transaction_type='spent_ai'
            )
            
            # Use AI service to analyze template
            analysis_result = AIService.analyze_template(template, request.user)
            
            # Track AI usage analytics
            AnalyticsService.track_event(
                user=request.user,
                event_name='ai_analysis_used',
                category='ai',
                properties={
                    'template_id': str(template.id),
                    'credits_spent': ai_cost,
                    'analysis_type': 'template_optimization'
                }
            )
            
            return Response({
                'analysis': analysis_result,
                'credits_spent': ai_cost,
                'remaining_credits': request.user.credits
            })
            
        except Exception as e:
            return Response(
                {'error': 'AI analysis failed. Please try again later.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """
        Get detailed analytics for a template (author only)
        """
        template = self.get_object()
        
        # Only allow template author or admin to view analytics
        if template.author != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Use analytics serializer to format data
        serializer = TemplateAnalyticsSerializer(template)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Create a copy of an existing template
        """
        original_template = self.get_object()
        
        # Create duplicate with modified title
        duplicate_title = f"{original_template.title} (Copy)"
        counter = 1
        while Template.objects.filter(title=duplicate_title, author=request.user).exists():
            duplicate_title = f"{original_template.title} (Copy {counter})"
            counter += 1
        
        with transaction.atomic():
            # Create new template
            new_template = Template.objects.create(
                title=duplicate_title,
                description=original_template.description,
                category=original_template.category,
                template_content=original_template.template_content,
                author=request.user,
                version="1.0.0",
                tags=original_template.tags.copy() if original_template.tags else [],
                is_public=False,  # Start as private
            )
            
            # Copy all fields
            for template_field in original_template.templatefield_set.all():
                new_field = PromptField.objects.create(
                    label=template_field.field.label,
                    placeholder=template_field.field.placeholder,
                    field_type=template_field.field.field_type,
                    is_required=template_field.field.is_required,
                    default_value=template_field.field.default_value,
                    validation_pattern=template_field.field.validation_pattern,
                    help_text=template_field.field.help_text,
                    options=template_field.field.options.copy() if template_field.field.options else [],
                    order=template_field.order
                )
                new_template.fields.add(new_field)
        
        # Track analytics
        AnalyticsService.track_event(
            user=request.user,
            event_name='template_duplicated',
            category='template',
            properties={
                'original_template_id': str(original_template.id),
                'new_template_id': str(new_template.id),
                'original_title': original_template.title
            }
        )
        
        serializer = TemplateDetailSerializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def search_suggestions(self, request):
        """
        Get search suggestions based on popular templates and tags
        """
        # Get popular tags
        from django.db.models import Count
        popular_tags = Template.objects.filter(
            is_active=True,
            is_public=True
        ).exclude(tags=[]).values_list('tags', flat=True)
        
        # Flatten and count tags
        all_tags = []
        for tag_list in popular_tags:
            all_tags.extend(tag_list)
        
        from collections import Counter
        tag_counts = Counter(all_tags)
        popular_tags = [tag for tag, count in tag_counts.most_common(10)]
        
        # Get popular categories
        popular_categories = TemplateCategory.objects.annotate(
            template_count=Count('templates', filter=Q(templates__is_active=True, templates__is_public=True))
        ).filter(template_count__gt=0).order_by('-template_count')[:5]
        
        return Response({
            'popular_tags': popular_tags,
            'popular_categories': [
                {'name': cat.name, 'slug': cat.slug, 'count': cat.template_count}
                for cat in popular_categories
            ]
        })


# New High-Performance Views for 100K Prompt Library and WebSocket Integration

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def search_prompts(request):
    """
    High-performance prompt search endpoint optimized for sub-50ms response times
    """
    start_time = time.time()
    
    # Check if services are available
    if not search_service:
        return Response(
            {'error': 'Search service not available - please check configuration'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Parse request data
        data = request.data
        query = data.get('query', '').strip()
        category = data.get('category')
        max_results = min(data.get('max_results', 20), 50)  # Limit for performance
        session_id = data.get('session_id')
        
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user intent if provided
        user_intent = None
        if data.get('intent_id'):
            try:
                user_intent = UserIntent.objects.get(id=data['intent_id'])
            except UserIntent.DoesNotExist:
                pass
        
        # Perform search
        results, metrics = search_service.search_prompts(
            query=query,
            user_intent=user_intent,
            category=category,
            max_results=max_results,
            session_id=session_id
        )
        
        # Format results for API response
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': str(result.prompt.id),
                'title': result.prompt.title,
                'content': result.prompt.content,
                'category': result.prompt.category,
                'subcategory': result.prompt.subcategory,
                'tags': result.prompt.tags,
                'keywords': result.prompt.keywords,
                'intent_category': result.prompt.intent_category,
                'usage_count': result.prompt.usage_count,
                'average_rating': result.prompt.average_rating,
                'quality_score': result.prompt.quality_score,
                'complexity_score': result.prompt.complexity_score,
                'score': round(result.score, 3),
                'relevance_reason': result.relevance_reason,
                'category_match': result.category_match,
                'intent_match': result.intent_match
            })
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log performance
        performance_monitor.record_response_time('search_api', response_time_ms)
        
        # Prepare response
        response_data = {
            'results': formatted_results,
            'total_results': len(formatted_results),
            'query': query,
            'category': category,
            'search_time_ms': metrics.get('total_time_ms', 0),
            'response_time_ms': response_time_ms,
            'from_cache': metrics.get('from_cache', False),
            'performance': {
                'sub_50ms': response_time_ms < 50,
                'cache_hit': metrics.get('from_cache', False),
                'optimization_suggestions': _get_optimization_suggestions(response_time_ms)
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Search API error: {e}")
        response_time_ms = int((time.time() - start_time) * 1000)
        performance_monitor.record_response_time('search_api_error', response_time_ms)
        
        return Response(
            {
                'error': 'Search failed',
                'details': str(e) if request.user.is_staff else 'Internal error',
                'response_time_ms': response_time_ms
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def process_intent(request):
    """
    Process user intent for WebSocket chat optimization
    """
    start_time = time.time()
    
    try:
        data = request.data
        query = data.get('query', '').strip()
        session_id = data.get('session_id')
        
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simple intent classification for now (can be enhanced with LangChain later)
        intent_category = _classify_intent_simple(query)
        
        # Save intent to database
        user = request.user if request.user.is_authenticated else None
        intent = UserIntent.objects.create(
            session_id=session_id or 'anonymous',
            user=user,
            original_query=query,
            processed_intent={'simple_classification': True},
            intent_category=intent_category,
            confidence_score=0.8,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return Response({
            'intent_id': str(intent.id),
            'intent_category': intent.intent_category,
            'confidence_score': intent.confidence_score,
            'keywords': _extract_keywords_simple(query),
            'context': f'Classified as {intent_category}',
            'processing_time_ms': intent.processing_time_ms,
            'response_time_ms': response_time_ms,
            'suggestions': _get_intent_suggestions(intent.intent_category)
        })
        
    except Exception as e:
        logger.error(f"Intent processing error: {e}")
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return Response(
            {
                'error': 'Intent processing failed',
                'details': str(e) if request.user.is_staff else 'Internal error',
                'response_time_ms': response_time_ms
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@cache_page(300)  # Cache for 5 minutes
def get_featured_prompts_library(request):
    """
    Get featured prompts from the 100K prompt library
    """
    start_time = time.time()
    
    try:
        category = request.GET.get('category')
        max_results = min(int(request.GET.get('max_results', 10)), 20)
        
        results = search_service.get_featured_prompts(
            category=category,
            max_results=max_results
        )
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': str(result.prompt.id),
                'title': result.prompt.title,
                'content': result.prompt.content[:300],  # Truncate for list view
                'category': result.prompt.category,
                'tags': result.prompt.tags[:5],  # Limit tags
                'average_rating': result.prompt.average_rating,
                'usage_count': result.prompt.usage_count,
                'quality_score': result.prompt.quality_score
            })
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return Response({
            'results': formatted_results,
            'total_results': len(formatted_results),
            'category': category,
            'response_time_ms': response_time_ms,
            'cached': True
        })
        
    except Exception as e:
        logger.error(f"Featured prompts error: {e}")
        return Response(
            {'error': 'Failed to fetch featured prompts'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_similar_prompts(request, prompt_id):
    """
    Get similar prompts from the library
    """
    start_time = time.time()
    
    try:
        max_results = min(int(request.GET.get('max_results', 5)), 10)
        
        results = search_service.similar_prompts(
            prompt_id=prompt_id,
            max_results=max_results
        )
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': str(result.prompt.id),
                'title': result.prompt.title,
                'content': result.prompt.content[:200],
                'category': result.prompt.category,
                'tags': result.prompt.tags[:3],
                'score': round(result.score, 3),
                'relevance_reason': result.relevance_reason
            })
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return Response({
            'results': formatted_results,
            'prompt_id': prompt_id,
            'response_time_ms': response_time_ms
        })
        
    except Exception as e:
        logger.error(f"Similar prompts error: {e}")
        return Response(
            {'error': 'Failed to fetch similar prompts'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def get_performance_metrics(request):
    """
    Get system performance metrics for admin monitoring
    """
    try:
        # Cache stats
        cache_stats = multi_cache.get_stats()
        
        # Performance monitor stats
        avg_search_time = performance_monitor.get_average_response_time('search_api')
        avg_websocket_time = performance_monitor.get_average_response_time('websocket')
        
        # Database stats
        total_prompts = PromptLibrary.objects.count()
        total_intents = UserIntent.objects.count()
        total_messages = ChatMessage.objects.count()
        
        # Recent performance metrics
        recent_metrics = PerformanceMetrics.objects.filter(
            operation_type__in=['search', 'websocket', 'optimization']
        ).order_by('-timestamp')[:100]
        
        metrics_summary = {}
        for metric in recent_metrics:
            op_type = metric.operation_type
            if op_type not in metrics_summary:
                metrics_summary[op_type] = {
                    'count': 0,
                    'total_time': 0,
                    'success_count': 0
                }
            
            metrics_summary[op_type]['count'] += 1
            metrics_summary[op_type]['total_time'] += metric.response_time_ms
            if metric.success:
                metrics_summary[op_type]['success_count'] += 1
        
        # Calculate averages
        for op_type in metrics_summary:
            data = metrics_summary[op_type]
            data['avg_response_time'] = data['total_time'] / data['count'] if data['count'] > 0 else 0
            data['success_rate'] = data['success_count'] / data['count'] if data['count'] > 0 else 0
        
        return Response({
            'cache': cache_stats,
            'performance': {
                'avg_search_time_ms': round(avg_search_time, 2),
                'avg_websocket_time_ms': round(avg_websocket_time, 2),
                'sub_50ms_target': {
                    'search_compliant': avg_search_time < 50,
                    'websocket_compliant': avg_websocket_time < 50
                }
            },
            'database': {
                'total_prompts': total_prompts,
                'total_intents': total_intents,
                'total_messages': total_messages
            },
            'operations': metrics_summary,
            'recommendations': performance_monitor.recommend_optimizations()
        })
        
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        return Response(
            {'error': 'Failed to fetch performance metrics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@method_decorator(csrf_exempt, name='dispatch')
class WebSocketHealthCheck(View):
    """
    Health check endpoint for WebSocket functionality
    """
    
    def get(self, request):
        """Check WebSocket system health"""
        try:
            health_data = {
                'websocket_available': True,
                'redis_connected': self._check_redis(),
                'cache_functional': self._check_cache(),
                'timestamp': time.time()
            }
            
            overall_health = all([
                health_data['redis_connected'],
                health_data['cache_functional']
            ])
            
            health_data['status'] = 'healthy' if overall_health else 'degraded'
            
            return JsonResponse(health_data)
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return JsonResponse({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }, status=500)
    
    def _check_redis(self) -> bool:
        """Check Redis connectivity"""
        try:
            cache.set('health_check', 'ok', 10)
            return cache.get('health_check') == 'ok'
        except Exception:
            return False
    
    def _check_cache(self) -> bool:
        """Check multi-level cache"""
        try:
            multi_cache.set('health_check', 'ok', 10)
            return multi_cache.get('health_check') == 'ok'
        except Exception:
            return False

# Utility functions

def _classify_intent_simple(query: str) -> str:
    """Simple intent classification based on keywords"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['write', 'create', 'draft', 'compose']):
        return 'content_creation'
    elif any(word in query_lower for word in ['technical', 'documentation', 'code', 'api']):
        return 'technical_writing'
    elif any(word in query_lower for word in ['email', 'message', 'letter', 'communication']):
        return 'communication'
    elif any(word in query_lower for word in ['analyze', 'analysis', 'research', 'study']):
        return 'analysis'
    elif any(word in query_lower for word in ['creative', 'story', 'brainstorm', 'idea']):
        return 'creative'
    elif any(word in query_lower for word in ['code', 'program', 'function', 'algorithm']):
        return 'coding'
    elif any(word in query_lower for word in ['business', 'proposal', 'report', 'presentation']):
        return 'business'
    elif any(word in query_lower for word in ['teach', 'learn', 'education', 'explain']):
        return 'education'
    else:
        return 'general'

def _extract_keywords_simple(query: str) -> list:
    """Simple keyword extraction"""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    words = query.lower().split()
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords[:5]  # Return top 5 keywords

def _get_optimization_suggestions(response_time_ms: int) -> list:
    """Get optimization suggestions based on response time"""
    suggestions = []
    
    if response_time_ms > 100:
        suggestions.append("Consider increasing cache timeout")
        suggestions.append("Review database query optimization")
    elif response_time_ms > 50:
        suggestions.append("Performance is above target - consider cache warming")
    else:
        suggestions.append("Performance is optimal")
    
    return suggestions

def _get_intent_suggestions(intent_category: str) -> list:
    """Get suggestions based on intent category"""
    suggestions_map = {
        'content_creation': [
            'Try refining your content goals',
            'Consider your target audience',
            'Specify the content format you need'
        ],
        'technical_writing': [
            'Define your technical level',
            'Specify documentation type',
            'Consider your audience expertise'
        ],
        'communication': [
            'Clarify your communication style',
            'Define your relationship with the recipient',
            'Specify the desired outcome'
        ],
        'general': [
            'Try being more specific about your needs',
            'Consider adding context to your request',
            'Think about your end goal'
        ]
    }
    
    return suggestions_map.get(intent_category, suggestions_map['general'])


