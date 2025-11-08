"""
MVP Template Views - Professional template management API

Clean, efficient template CRUD operations for production MVP.
Focuses on essential functionality with proper pagination and search.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Q, Count, Avg
from django.utils import timezone
import logging

from .models import Template, TemplateCategory
from .serializers import (
    TemplateListSerializer, TemplateDetailSerializer, 
    TemplateCreateUpdateSerializer, TemplateCategorySerializer
)

logger = logging.getLogger(__name__)


class MVPPagination(PageNumberPagination):
    """Standard pagination for MVP API"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class MVPTemplateCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    MVP Template Categories
    
    Read-only access to template categories with template counts.
    """
    
    queryset = TemplateCategory.objects.filter(is_active=True).order_by('order', 'name')
    serializer_class = TemplateCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = MVPPagination

    def get_queryset(self):
        """Optimize queryset with annotations"""
        return self.queryset.annotate(
            template_count=Count('templates', filter=Q(templates__is_active=True, templates__is_public=True))
        )

    @action(detail=True, methods=['get'])
    def templates(self, request, pk=None):
        """Get templates in this category"""
        try:
            category = self.get_object()
            templates = Template.objects.filter(
                category=category,
                is_active=True,
                is_public=True
            ).select_related('author', 'category').order_by('-created_at')
            
            # Paginate results
            page = self.paginate_queryset(templates)
            if page is not None:
                serializer = TemplateListSerializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            
            serializer = TemplateListSerializer(templates, many=True, context={'request': request})
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error fetching category templates: {e}")
            return Response({
                'error': 'Failed to fetch templates for this category'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MVPTemplateViewSet(viewsets.ModelViewSet):
    """
    MVP Template CRUD
    
    Complete template management with search, filtering, and pagination.
    Optimized for performance and ease of use.
    """
    
    queryset = Template.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = MVPPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_featured', 'is_public', 'author']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'title', 'usage_count']
    ordering = ['-created_at']

    def get_queryset(self):
        """Optimize queryset based on user and action"""
        queryset = Template.objects.filter(is_active=True)
        
        # Optimize database queries
        queryset = queryset.select_related('author', 'category').prefetch_related('fields')
        
        if self.action == 'list':
            # Show public templates unless user requests their own
            if self.request.query_params.get('my_templates') == 'true':
                if self.request.user.is_authenticated:
                    queryset = queryset.filter(author=self.request.user)
                else:
                    queryset = queryset.none()
            else:
                queryset = queryset.filter(is_public=True)
        
        return queryset

    def get_serializer_class(self):
        """Choose appropriate serializer"""
        if self.action == 'list':
            return TemplateListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TemplateCreateUpdateSerializer
        return TemplateDetailSerializer

    def perform_create(self, serializer):
        """Handle template creation"""
        try:
            template = serializer.save(author=self.request.user)
            logger.info(f"Template created: {template.id} by {self.request.user.username}")
        except Exception as e:
            logger.error(f"Template creation failed: {e}")
            raise

    def perform_update(self, serializer):
        """Handle template updates"""
        try:
            template = serializer.save()
            template.updated_at = timezone.now()
            template.save(update_fields=['updated_at'])
            logger.info(f"Template updated: {template.id} by {self.request.user.username}")
        except Exception as e:
            logger.error(f"Template update failed: {e}")
            raise

    def perform_destroy(self, instance):
        """Soft delete template"""
        try:
            instance.is_active = False
            instance.save(update_fields=['is_active'])
            logger.info(f"Template deleted: {instance.id} by {self.request.user.username}")
        except Exception as e:
            logger.error(f"Template deletion failed: {e}")
            raise

    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """Track template usage"""
        try:
            template = self.get_object()
            
            # Increment usage count
            template.usage_count = (template.usage_count or 0) + 1
            template.save(update_fields=['usage_count'])
            
            return Response({
                'message': 'Template usage recorded',
                'usage_count': template.usage_count
            })
            
        except Exception as e:
            logger.error(f"Template usage tracking failed: {e}")
            return Response({
                'error': 'Failed to record template usage'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def my_templates(self, request):
        """Get current user's templates"""
        if not request.user.is_authenticated:
            return Response({
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            templates = self.get_queryset().filter(author=request.user)
            
            page = self.paginate_queryset(templates)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(templates, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error fetching user templates: {e}")
            return Response({
                'error': 'Failed to fetch your templates'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def mvp_search_templates(request):
    """
    MVP Template Search
    
    Simple, efficient template search with pagination.
    """
    try:
        query = request.GET.get('q', '').strip()
        category_id = request.GET.get('category')
        
        if not query and not category_id:
            return Response({
                'error': 'Search query or category required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build query
        templates = Template.objects.filter(is_active=True, is_public=True)
        
        if query:
            templates = templates.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            )
        
        if category_id:
            templates = templates.filter(category_id=category_id)
        
        # Order by relevance (usage count for now)
        templates = templates.select_related('author', 'category').order_by('-usage_count', '-created_at')
        
        # Apply pagination
        paginator = MVPPagination()
        page = paginator.paginate_queryset(templates, request)
        
        if page is not None:
            serializer = TemplateListSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        serializer = TemplateListSerializer(templates, many=True, context={'request': request})
        return Response({
            'results': serializer.data,
            'count': templates.count()
        })
        
    except Exception as e:
        logger.error(f"Template search failed: {e}")
        return Response({
            'error': 'Search failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def mvp_featured_templates(request):
    """
    MVP Featured Templates
    
    Returns featured templates for homepage/discovery.
    """
    try:
        templates = Template.objects.filter(
            is_active=True,
            is_public=True,
            is_featured=True
        ).select_related('author', 'category').order_by('-created_at')[:10]
        
        serializer = TemplateListSerializer(templates, many=True, context={'request': request})
        
        return Response({
            'featured_templates': serializer.data,
            'count': len(serializer.data)
        })
        
    except Exception as e:
        logger.error(f"Featured templates fetch failed: {e}")
        return Response({
            'error': 'Failed to fetch featured templates'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def mvp_system_status(request):
    """
    MVP System Status
    
    Basic system health check with template statistics.
    """
    try:
        total_templates = Template.objects.filter(is_active=True, is_public=True).count()
        total_categories = TemplateCategory.objects.filter(is_active=True).count()
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'statistics': {
                'total_templates': total_templates,
                'total_categories': total_categories,
                'api_version': 'mvp-1.0'
            }
        })
        
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        return Response({
            'status': 'error',
            'error': 'System status check failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)