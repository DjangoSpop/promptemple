from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, F
from django.utils import timezone
from django.db import transaction

from .models import Template, TemplateCategory
from .serializers import (
    TemplateListSerializer, TemplateDetailSerializer, 
    TemplateCreateUpdateSerializer, TemplateCategorySerializer,
    TemplateUsageSerializer, TemplateRatingSerializer,
    TemplateAnalyticsSerializer
)
from apps.analytics.services import AnalyticsService
from apps.ai_services.services import AIService
from apps.gamification.services import GamificationService


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


