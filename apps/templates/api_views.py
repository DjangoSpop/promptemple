# """
# API Views for Templates with Infinite Scrolling, Suggestions, and Freemium Features
# Provides modern API endpoints for the frontend with pagination, search, and monetization
# """

# from rest_framework import viewsets, status, filters
# from rest_framework.decorators import action, api_view, permission_classes
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.pagination import PageNumberPagination
# from django_filters.rest_framework import DjangoFilterBackend
# from django.db.models import Q, Count, Avg, F
# from django.utils import timezone
# from django.core.cache import cache
# from django.contrib.auth import get_user_model

# from .models import Template, TemplateCategory, TemplateUsage, TemplateRating
# from .serializers import (
#     TemplateListSerializer, TemplateDetailSerializer, TemplateCategorySerializer,
#     TemplateUsageSerializer, SuggestionSerializer
# )
# from .services.suggestion_service import SuggestionAPIService
# from apps.billing.models import UserSubscription
# from apps.analytics.models import AnalyticsEvent

# User = get_user_model()


# class InfiniteScrollPagination(PageNumberPagination):
#     """Custom pagination for infinite scrolling"""
#     page_size = 12
#     page_size_query_param = 'page_size'
#     max_page_size = 50
#     #
#     def get_paginated_response(self, data):
#         """Enhanced pagination response with infinite scroll metadata"""
#         return Response({
#             'next': self.get_next_link(),
#             'previous': self.get_previous_link(),
#             'count': self.page.paginator.count,
#             'total_pages': self.page.paginator.num_pages,
#             'current_page': self.page.number,
#             'page_size': self.page_size,
#             'has_next': self.page.has_next(),
#             'has_previous': self.page.has_previous(),
#             'results': data,
#             # Infinite scroll specific
#             'load_more_url': self.get_next_link(),
#             'is_last_page': not self.page.has_next(),
#         })


# class TemplateViewSet(viewsets.ReadOnlyModelViewSet):
#     """ViewSet for template browsing with infinite scroll and search"""
    
#     serializer_class = TemplateListSerializer
#     pagination_class = InfiniteScrollPagination
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = ['category', 'is_featured', 'tags']
#     search_fields = ['title', 'description', 'tags']
#     ordering_fields = ['created_at', 'popularity_score', 'average_rating', 'usage_count']
#     ordering = ['-popularity_score', '-created_at']
    
#     def get_queryset(self):
#         """Get filtered queryset based on user and request parameters"""
#         queryset = Template.objects.filter(
#             is_active=True,
#             is_public=True
#         ).select_related('category', 'author').prefetch_related('fields')
        
#         # Apply additional filters
#         category_slug = self.request.query_params.get('category_slug')
#         if category_slug:
#             queryset = queryset.filter(category__slug=category_slug)
        
#         difficulty = self.request.query_params.get('difficulty')
#         if difficulty:
#             if difficulty == 'simple':
#                 queryset = queryset.annotate(field_count=Count('fields')).filter(field_count__lte=3)
#             elif difficulty == 'medium':
#                 queryset = queryset.annotate(field_count=Count('fields')).filter(field_count__range=(4, 7))
#             elif difficulty == 'complex':
#                 queryset = queryset.annotate(field_count=Count('fields')).filter(field_count__gte=8)
        
#         # Filter by rating
#         min_rating = self.request.query_params.get('min_rating')
#         if min_rating:
#             try:
#                 queryset = queryset.filter(average_rating__gte=float(min_rating))
#             except ValueError:
#                 pass
        
#         return queryset
    
#     def get_serializer_class(self):
#         """Use detailed serializer for retrieve action"""
#         if self.action == 'retrieve':
#             return TemplateDetailSerializer
#         return TemplateListSerializer
    
#     def list(self, request, *args, **kwargs):
#         """Enhanced list with analytics tracking"""
#         # Track browsing event
#         if request.user.is_authenticated:
#             self._track_browse_event(request)
        
#         response = super().list(request, *args, **kwargs)
        
#         # Add ad slots for infinite scroll
#         if hasattr(response, 'data') and 'results' in response.data:
#             response.data = self._inject_ad_slots(response.data, request)
        
#         return response
    
#     def retrieve(self, request, *args, **kwargs):
#         """Enhanced retrieve with view tracking and freemium checks"""
#         template = self.get_object()
        
#         # Track template view
#         self._track_template_view(request, template)
        
#         # Check freemium limitations
#         can_access, limitation_reason = self._check_template_access(request.user, template)
        
#         response = super().retrieve(request, *args, **kwargs)
        
#         # Add access information to response
#         if hasattr(response, 'data'):
#             response.data['access_info'] = {
#                 'can_access': can_access,
#                 'limitation_reason': limitation_reason,
#                 'is_premium_required': self._is_premium_template(template),
#                 'user_is_premium': self._is_user_premium(request.user),
#             }
        
#         return response
    
#     @action(detail=False, methods=['get'])
#     def featured(self, request):
#         """Get featured templates"""
#         featured_templates = self.get_queryset().filter(is_featured=True)[:6]
#         serializer = self.get_serializer(featured_templates, many=True)
#         return Response({
#             'featured_templates': serializer.data,
#             'total_count': featured_templates.count(),
#         })
    
#     @action(detail=False, methods=['get'])
#     def trending(self, request):
#         """Get trending templates based on recent usage"""
#         # Get templates with high recent usage
#         recent_date = timezone.now() - timezone.timedelta(days=7)
#         trending = self.get_queryset().annotate(
#             recent_usage=Count('usage_logs', filter=Q(usage_logs__started_at__gte=recent_date))
#         ).filter(recent_usage__gt=0).order_by('-recent_usage', '-popularity_score')[:10]
        
#         serializer = self.get_serializer(trending, many=True)
#         return Response({
#             'trending_templates': serializer.data,
#             'period': 'last_7_days',
#         })
    
#     @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
#     def use_template(self, request, pk=None):
#         """Start using a template (with freemium checks)"""
#         template = self.get_object()
#         user = request.user
        
#         # Check access limitations
#         can_access, limitation_reason = self._check_template_access(user, template)
        
#         if not can_access:
#             return Response({
#                 'error': 'Access denied',
#                 'reason': limitation_reason,
#                 'premium_required': True,
#                 'upgrade_url': '/pricing/',
#             }, status=status.HTTP_403_FORBIDDEN)
        
#         # Create usage session
#         usage = TemplateUsage.objects.create(
#             template=template,
#             user=user,
#             device_type=self._get_device_type(request),
#             app_version=request.META.get('HTTP_X_APP_VERSION', ''),
#         )
        
#         # Track analytics
#         self._track_template_usage_start(request, template)
        
#         # Update template usage count
#         Template.objects.filter(id=template.id).update(usage_count=F('usage_count') + 1)
        
#         return Response({
#             'usage_id': str(usage.id),
#             'template': TemplateDetailSerializer(template).data,
#             'message': 'Template usage started successfully',
#         })
    
#     @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
#     def complete_template(self, request, pk=None):
#         """Complete template usage"""
#         template = self.get_object()
#         user = request.user
        
#         # Find the most recent usage session
#         usage = TemplateUsage.objects.filter(
#             template=template,
#             user=user,
#             was_completed=False
#         ).order_by('-started_at').first()
        
#         if not usage:
#             return Response({
#                 'error': 'No active usage session found'
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         # Update usage session
#         usage.was_completed = True
#         usage.completed_at = timezone.now()
#         usage.time_spent_seconds = (usage.completed_at - usage.started_at).total_seconds()
#         usage.field_completion_data = request.data.get('field_data', {})
#         usage.generated_prompt_length = len(request.data.get('generated_prompt', ''))
#         usage.save()
        
#         # Track completion analytics
#         self._track_template_completion(request, template, usage)
        
#         # Update user stats
#         if hasattr(user, 'templates_completed'):
#             User.objects.filter(id=user.id).update(
#                 templates_completed=F('templates_completed') + 1
#             )
        
#         return Response({
#             'message': 'Template completed successfully',
#             'usage_time': usage.time_spent_seconds,
#             'completion_rate': usage.completion_rate_percentage,
#         })
    
#     @action(detail=False, methods=['get'])
#     def suggestions(self, request):
#         """Get personalized template suggestions"""
#         suggestion_service = SuggestionAPIService()
        
#         if request.user.is_authenticated:
#             suggestions = suggestion_service.get_home_suggestions(request.user, limit=6)
#         else:
#             suggestions = suggestion_service.get_home_suggestions(None, limit=6)
        
#         return Response(suggestions)
    
#     @action(detail=True, methods=['get'])
#     def similar(self, request, pk=None):
#         """Get similar templates"""
#         template = self.get_object()
#         suggestion_service = SuggestionAPIService()
        
#         similar = suggestion_service.get_similar_templates(
#             str(template.id), 
#             request.user if request.user.is_authenticated else None,
#             limit=5
#         )
        
#         return Response(similar)
    
#     def _check_template_access(self, user, template):
#         """Check if user can access template based on freemium rules"""
#         if not user.is_authenticated:
#             # Anonymous users get limited access
#             return True, None  # Allow for demo purposes
        
#         # Check if user is premium
#         if self._is_user_premium(user):
#             return True, None
        
#         # Check daily usage limits for free users
#         today = timezone.now().date()
#         daily_usage = TemplateUsage.objects.filter(
#             user=user,
#             started_at__date=today
#         ).count()
        
#         DAILY_FREE_LIMIT = 5  # Free users get 5 template uses per day
        
#         if daily_usage >= DAILY_FREE_LIMIT:
#             return False, f'Daily limit reached ({DAILY_FREE_LIMIT} templates per day for free users)'
        
#         # Check if template is premium-only
#         if self._is_premium_template(template):
#             return False, 'This template requires a premium subscription'
        
#         return True, None
    
#     def _is_user_premium(self, user):
#         """Check if user has active premium subscription"""
#         if not user.is_authenticated:
#             return False
        
#         try:
#             subscription = UserSubscription.objects.get(user=user)
#             return subscription.is_premium  # Use the property method
#         except UserSubscription.DoesNotExist:
#             return False
    
#     def _is_premium_template(self, template):
#         """Check if template requires premium access"""
#         # Mark templates as premium based on certain criteria
#         return (
#             template.is_featured or 
#             template.popularity_score > 80 or
#             template.field_count > 10 or
#             'premium' in template.tags
#         )
    
#     def _inject_ad_slots(self, response_data, request):
#         """Inject ad slots into infinite scroll results"""
#         results = response_data.get('results', [])
        
#         if len(results) == 0:
#             return response_data
        
#         # Inject ads every 4 templates for free users
#         if not self._is_user_premium(request.user):
#             ad_positions = [4, 8, 12]  # Insert ads at these positions
            
#             for pos in ad_positions:
#                 if pos < len(results):
#                     ad_slot = {
#                         'type': 'advertisement',
#                         'id': f'ad_slot_{pos}',
#                         'title': 'Upgrade to Premium',
#                         'description': 'Get unlimited access to all templates',
#                         'cta_text': 'Upgrade Now',
#                         'cta_url': '/pricing/',
#                         'ad_type': 'premium_upgrade',
#                     }
#                     results.insert(pos, ad_slot)
        
#         response_data['results'] = results
#         return response_data
    
#     def _track_browse_event(self, request):
#         """Track browsing analytics"""
#         if request.user.is_authenticated:
#             AnalyticsEvent.objects.create(
#                 user=request.user,
#                 event_type='category_browse',
#                 event_name='category_browse',
#                 properties={
#                     'page': request.query_params.get('page', 1),
#                     'category': request.query_params.get('category_slug'),
#                     'search': request.query_params.get('search'),
#                     'ordering': request.query_params.get('ordering'),
#                 }
#             )
    
#     def _track_template_view(self, request, template):
#         """Track template view analytics"""
#         if request.user.is_authenticated:
#             AnalyticsEvent.objects.create(
#                 user=request.user,
#                 event_type='template_view',
#                 event_name='template_view',
#                 properties={
#                     'template_id': str(template.id),
#                     'template_title': template.title,
#                     'category': template.category.name,
#                     'is_featured': template.is_featured,
#                 }
#             )
    
#     def _track_template_usage_start(self, request, template):
#         """Track template usage start"""
#         if request.user.is_authenticated:
#             AnalyticsEvent.objects.create(
#                 user=request.user,
#                 event_type='template_usage_start',
#                 event_name='template_usage_start',
#                 properties={
#                     'template_id': str(template.id),
#                     'template_title': template.title,
#                     'category': template.category.name,
#                     'field_count': template.field_count,
#                 }
#             )
    
#     def _track_template_completion(self, request, template, usage):
#         """Track template completion"""
#         if request.user.is_authenticated:
#             AnalyticsEvent.objects.create(
#                 user=request.user,
#                 event_type='template_completion',
#                 event_name='template_completion',
#                 properties={
#                     'template_id': str(template.id),
#                     'template_title': template.title,
#                     'category': template.category.name,
#                     'completion_time_seconds': usage.time_spent_seconds,
#                     'completion_rate': usage.completion_rate_percentage,
#                 }
#             )
    
#     def _get_device_type(self, request):
#         """Detect device type from request"""
#         user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
#         if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
#             return 'mobile'
#         elif 'tablet' in user_agent or 'ipad' in user_agent:
#             return 'tablet'
#         else:
#             return 'desktop'


# class TemplateCategoryViewSet(viewsets.ReadOnlyModelViewSet):
#     """ViewSet for template categories"""
    
#     queryset = TemplateCategory.objects.filter(is_active=True).order_by('order', 'name')
#     serializer_class = TemplateCategorySerializer
    
#     @action(detail=True, methods=['get'])
#     def templates(self, request, pk=None):
#         """Get templates for a specific category with infinite scroll"""
#         category = self.get_object()
        
#         templates = Template.objects.filter(
#             category=category,
#             is_active=True,
#             is_public=True
#         ).order_by('-popularity_score', '-created_at')
        
#         # Apply pagination
#         paginator = InfiniteScrollPagination()
#         page = paginator.paginate_queryset(templates, request)
        
#         if page is not None:
#             serializer = TemplateListSerializer(page, many=True)
#             return paginator.get_paginated_response(serializer.data)
        
#         serializer = TemplateListSerializer(templates, many=True)
#         return Response(serializer.data)
    
#     @action(detail=False, methods=['get'])
#     def with_counts(self, request):
#         """Get categories with template counts"""
#         categories = self.get_queryset().annotate(
#             template_count=Count('templates', filter=Q(templates__is_active=True, templates__is_public=True))
#         )
        
#         serializer = self.get_serializer(categories, many=True)
#         return Response(serializer.data)


# @api_view(['GET'])
# @permission_classes([AllowAny])
# def search_templates(request):
#     """Advanced template search with autocomplete"""
#     query = request.GET.get('q', '').strip()
#     category = request.GET.get('category')
#     limit = min(int(request.GET.get('limit', 10)), 20)
    
#     if not query:
#         return Response({'results': []})
    
#     # Build search query
#     search_q = Q(title__icontains=query) | Q(description__icontains=query) | Q(tags__icontains=query)
    
#     templates = Template.objects.filter(
#         search_q,
#         is_active=True,
#         is_public=True
#     )
    
#     if category:
#         templates = templates.filter(category__slug=category)
    
#     templates = templates.order_by('-popularity_score')[:limit]
    
#     # Track search analytics
#     if request.user.is_authenticated:
#         AnalyticsEvent.objects.create(
#             user=request.user,
#             event_type='template_search',
#             event_name='template_search',
#             properties={
#                 'search_term': query,
#                 'category': category,
#                 'results_count': templates.count(),
#             }
#         )
    
#     serializer = TemplateListSerializer(templates, many=True)
#     return Response({
#         'query': query,
#         'results': serializer.data,
#         'total_count': templates.count(),
#     })


# @api_view(['GET'])
# @permission_classes([AllowAny])
# def autocomplete_search(request):
#     """Autocomplete search suggestions"""
#     query = request.GET.get('q', '').strip()
    
#     if len(query) < 2:
#         return Response({'suggestions': []})
    
#     # Get templates matching the query
#     templates = Template.objects.filter(
#         Q(title__icontains=query) | Q(tags__icontains=query),
#         is_active=True,
#         is_public=True
#     )[:5]
    
#     # Get categories matching the query
#     categories = TemplateCategory.objects.filter(
#         name__icontains=query,
#         is_active=True
#     )[:3]
    
#     suggestions = []
    
#     # Add template suggestions
#     for template in templates:
#         suggestions.append({
#             'type': 'template',
#             'title': template.title,
#             'category': template.category.name,
#             'url': f'/templates/{template.id}/',
#         })
    
#     # Add category suggestions
#     for category in categories:
#         suggestions.append({
#             'type': 'category',
#             'title': category.name,
#             'description': category.description,
#             'url': f'/categories/{category.slug}/',
#         })
    
#     return Response({
#         'query': query,
#         'suggestions': suggestions,
#     })


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def copy_template_content(request):
#     """Copy template content (with freemium limits)"""
#     template_id = request.data.get('template_id')
    
#     if not template_id:
#         return Response({
#             'error': 'Template ID is required'
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     try:
#         template = Template.objects.get(id=template_id, is_active=True)
#     except Template.DoesNotExist:
#         return Response({
#             'error': 'Template not found'
#         }, status=status.HTTP_404_NOT_FOUND)
    
#     user = request.user
    
#     # Check copy limits for free users
#     if not _is_user_premium_copy(user):
#         today = timezone.now().date()
#         daily_copies = TemplateUsage.objects.filter(
#             user=user,
#             started_at__date=today,
#             # Add copy tracking field if needed
#         ).count()
        
#         DAILY_COPY_LIMIT = 3
#         if daily_copies >= DAILY_COPY_LIMIT:
#             return Response({
#                 'error': 'Daily copy limit reached',
#                 'limit': DAILY_COPY_LIMIT,
#                 'premium_required': True,
#                 'upgrade_url': '/pricing/',
#             }, status=status.HTTP_403_FORBIDDEN)
    
#     # Track the copy event
#     # You might want to create a separate model for copy tracking
    
#     return Response({
#         'template_content': template.template_content,
#         'template_title': template.title,
#         'copies_remaining': max(0, 3 - daily_copies - 1) if not _is_user_premium_copy(user) else None,
#     })


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def user_usage_stats(request):
#     """Get user usage statistics"""
#     user = request.user
#     today = timezone.now().date()
    
#     # Daily usage
#     daily_templates = TemplateUsage.objects.filter(
#         user=user,
#         started_at__date=today
#     ).count()
    
#     daily_copies = 0  # Implement copy tracking if needed
    
#     # Get subscription info
#     is_premium = _is_user_premium_copy(user)
    
#     return Response({
#         'templates_used_today': daily_templates,
#         'copies_made_today': daily_copies,
#         'daily_template_limit': None if is_premium else 5,
#         'daily_copy_limit': None if is_premium else 3,
#         'is_premium': is_premium,
#         'templates_remaining': None if is_premium else max(0, 5 - daily_templates),
#         'copies_remaining': None if is_premium else max(0, 3 - daily_copies),
#     })


# @api_view(['GET'])
# @permission_classes([AllowAny])
# def freemium_info(request):
#     """Get freemium feature information"""
#     if request.user.is_authenticated:
#         is_premium = _is_user_premium_copy(request.user)
#     else:
#         is_premium = False
    
#     return Response({
#         'is_premium': is_premium,
#         'daily_limits': {
#             'templates': None if is_premium else 5,
#             'copies': None if is_premium else 3,
#         },
#         'features_available': [
#             'basic_templates',
#             'search',
#             'categories',
#         ] + (['premium_templates', 'unlimited_usage', 'priority_support'] if is_premium else []),
#         'features_locked': [] if is_premium else [
#             'premium_templates',
#             'unlimited_usage',
#             'advanced_analytics',
#             'priority_support',
#         ],
#         'upgrade_benefits': [
#             'Unlimited template usage',
#             'Access to premium templates',
#             'No advertisements',
#             'Priority customer support',
#             'Advanced analytics',
#         ] if not is_premium else [],
#     })


# def _is_user_premium_copy(user):
#     """Helper function to check premium status for copy operations"""
#     if not user.is_authenticated:
#         return False
    
#     try:
#         subscription = UserSubscription.objects.get(user=user)
#         return subscription.is_premium
#     except UserSubscription.DoesNotExist:
#         return False