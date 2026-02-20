from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import PromptHistory, SavedPrompt, PromptIteration, ConversationThread
from .serializers import (
    PromptHistorySerializer, PromptHistoryCreateSerializer, PromptHistoryUpdateSerializer,
    SavedPromptSerializer, SavedPromptCreateSerializer, SavedPromptUpdateSerializer, SavedPromptListSerializer,
    PromptIterationSerializer, PromptIterationCreateSerializer,
    ConversationThreadSerializer, ConversationThreadCreateSerializer
)
from apps.prompt_history.services.optimization import enhance_prompt
from django.conf import settings
import logging

# Import drf-spectacular decorators
try:
    from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
    from drf_spectacular.types import OpenApiTypes
    DRF_SPECTACULAR_AVAILABLE = True
except ImportError:
    # Fallback decorator that does nothing if drf-spectacular is not installed
    def extend_schema(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def extend_schema_view(*args, **kwargs):
        def decorator(cls):
            return cls
        return decorator
    OpenApiParameter = None
    OpenApiExample = None
    OpenApiTypes = None
    DRF_SPECTACULAR_AVAILABLE = False

logger = logging.getLogger(__name__)


class IsOwnerOrStaff(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.user and (request.user.is_staff or obj.user_id == request.user.id)


class PromptHistoryViewSet(viewsets.ModelViewSet):
    queryset = PromptHistory.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['intent_category', 'source']
    search_fields = ['original_prompt']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = PromptHistory.objects.filter(is_deleted=False)
        # owners see their own, staff can see all
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create']:
            return PromptHistoryCreateSerializer
        if self.action in ['partial_update', 'update']:
            return PromptHistoryUpdateSerializer
        return PromptHistorySerializer

    def perform_destroy(self, instance):
        instance.soft_delete()

    @action(detail=True, methods=['post'])
    def enhance(self, request, pk=None):
        """Run optimization pipeline, debit credits, update optimized_prompt"""
        instance = get_object_or_404(PromptHistory, pk=pk, is_deleted=False)
        if instance.user != request.user and not request.user.is_staff:
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        model = request.data.get('model')
        style = request.data.get('style')
        start = timezone.now()

        try:
            result = enhance_prompt(instance.original_prompt, {
                'user_id': request.user.id,
                'session_id': (request.data.get('session_id') or instance.meta.get('session_id'))
            }, model=model, style=style)

            # debit credits (stub) - safe no-op if not available
            cost = result.get('credits_spent', 1)
            try:
                from apps.gamification.services import GamificationService
                GamificationService.spend_credits(user=request.user, amount=cost, reason='enhance_prompt', transaction_type='enhance')
            except Exception:
                logger.debug('Gamification spend_credits failed or not available')

            instance.optimized_prompt = result.get('optimized_prompt')
            instance.model_used = result.get('model_used', '')
            instance.tokens_input = result.get('tokens_input', 0)
            instance.tokens_output = result.get('tokens_output', 0)
            instance.credits_spent = instance.credits_spent + result.get('credits_spent', 0)
            meta = instance.meta or {}
            meta.update(result.get('meta', {}))
            instance.meta = meta
            instance.save()

            return Response({
                'optimized_prompt': instance.optimized_prompt,
                'model_used': instance.model_used,
                'tokens_input': instance.tokens_input,
                'tokens_output': instance.tokens_output,
                'credits_spent': instance.credits_spent,
                'meta': instance.meta,
            })

        except Exception as e:
            logger.exception('Enhance failed')
            return Response({'error': 'Enhance failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== SavedPrompt ViewSet ====================

@extend_schema_view(
    list=extend_schema(
        summary="List saved prompts",
        description="Get all saved prompts for the authenticated user with optional filtering.",
        parameters=[
            OpenApiParameter(name='category', description='Filter by category', required=False, type=str),
            OpenApiParameter(name='is_favorite', description='Filter by favorite status', required=False, type=bool),
            OpenApiParameter(name='search', description='Search in title, content, description', required=False, type=str),
        ] if OpenApiParameter else [],
        tags=['Saved Prompts']
    ),
    create=extend_schema(
        summary="Create saved prompt",
        description="Save a new plain prompt for future reuse.",
        tags=['Saved Prompts']
    ),
    retrieve=extend_schema(
        summary="Get saved prompt",
        description="Retrieve a specific saved prompt by ID.",
        tags=['Saved Prompts']
    ),
    update=extend_schema(
        summary="Update saved prompt",
        description="Update an existing saved prompt.",
        tags=['Saved Prompts']
    ),
    partial_update=extend_schema(
        summary="Partial update saved prompt",
        description="Partially update an existing saved prompt.",
        tags=['Saved Prompts']
    ),
    destroy=extend_schema(
        summary="Delete saved prompt",
        description="Soft-delete a saved prompt (can be recovered).",
        tags=['Saved Prompts']
    ),
)
class SavedPromptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user's saved plain prompts.
    
    Provides CRUD operations for prompts that users want to save for future reuse.
    This is independent from the iteration/history system - just simple prompt storage.
    
    **Also available via GraphQL at `/api/graphql/`**
    """
    queryset = SavedPrompt.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_favorite', 'is_public']
    search_fields = ['title', 'content', 'description']
    ordering_fields = ['created_at', 'updated_at', 'use_count', 'title']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Return only the user's own saved prompts (non-deleted)"""
        qs = SavedPrompt.objects.filter(is_deleted=False)
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return SavedPromptCreateSerializer
        if self.action in ['update', 'partial_update']:
            return SavedPromptUpdateSerializer
        if self.action == 'list':
            return SavedPromptListSerializer
        return SavedPromptSerializer

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete"""
        instance.soft_delete()

    @extend_schema(
        summary="Toggle favorite status",
        description="Add or remove a prompt from favorites.",
        responses={200: SavedPromptSerializer},
        tags=['Saved Prompts']
    )
    @action(detail=True, methods=['post'], url_path='toggle-favorite')
    def toggle_favorite(self, request, pk=None):
        """Toggle the favorite status of a saved prompt"""
        instance = self.get_object()
        new_status = instance.toggle_favorite()
        return Response({
            'id': str(instance.id),
            'is_favorite': new_status,
            'message': f"Prompt {'added to' if new_status else 'removed from'} favorites"
        })

    @extend_schema(
        summary="Mark prompt as used",
        description="Record that a prompt was used (increments use count).",
        responses={200: SavedPromptSerializer},
        tags=['Saved Prompts']
    )
    @action(detail=True, methods=['post'], url_path='use')
    def use_prompt(self, request, pk=None):
        """Mark a saved prompt as used, incrementing the use count"""
        instance = self.get_object()
        instance.increment_use_count()
        return Response({
            'id': str(instance.id),
            'use_count': instance.use_count,
            'last_used_at': instance.last_used_at.isoformat() if instance.last_used_at else None,
            'message': 'Prompt usage recorded'
        })

    @extend_schema(
        summary="Duplicate a prompt",
        description="Create a copy of an existing saved prompt.",
        responses={201: SavedPromptSerializer},
        tags=['Saved Prompts']
    )
    @action(detail=True, methods=['post'], url_path='duplicate')
    def duplicate(self, request, pk=None):
        """Create a copy of an existing saved prompt"""
        original = self.get_object()
        new_title = request.data.get('new_title') or f"{original.title} (Copy)"
        
        duplicate = SavedPrompt.objects.create(
            user=request.user,
            title=new_title,
            content=original.content,
            description=original.description,
            category=original.category,
            tags=original.tags.copy() if original.tags else [],
            is_favorite=False,
            is_public=False,
            metadata=original.metadata.copy() if original.metadata else {},
        )
        
        serializer = SavedPromptSerializer(duplicate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Get favorite prompts",
        description="Get all prompts marked as favorite.",
        responses={200: SavedPromptListSerializer(many=True)},
        tags=['Saved Prompts']
    )
    @action(detail=False, methods=['get'], url_path='favorites')
    def favorites(self, request):
        """Get all favorite saved prompts"""
        queryset = self.get_queryset().filter(is_favorite=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SavedPromptListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SavedPromptListSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get public prompts",
        description="Get prompts shared publicly by all users.",
        responses={200: SavedPromptListSerializer(many=True)},
        parameters=[
            OpenApiParameter(name='category', description='Filter by category', required=False, type=str),
        ] if OpenApiParameter else [],
        tags=['Saved Prompts']
    )
    @action(detail=False, methods=['get'], url_path='public')
    def public_prompts(self, request):
        """Get public prompts from all users"""
        queryset = SavedPrompt.objects.filter(is_public=True, is_deleted=False)
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        queryset = queryset.order_by('-use_count', '-updated_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SavedPromptListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SavedPromptListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Get summary statistics for the user's saved prompts"""
        qs = self.get_queryset()
        total = qs.count()
        favorites = qs.filter(is_favorite=True).count()
        public = qs.filter(is_public=True).count()
        total_uses = qs.aggregate(total=Sum('use_count'))['total'] or 0

        # Most-used categories (top 5)
        categories = (
            qs.exclude(category='')
            .values('category')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        return Response({
            'total': total,
            'favorites': favorites,
            'public': public,
            'total_uses': total_uses,
            'top_categories': list(categories),
        })

    @action(detail=True, methods=['get', 'post'], url_path='iterations')
    def iterations(self, request, pk=None):
        """
        List or create prompt iterations for a specific saved prompt.

        GET  /saved-prompts/{id}/iterations/  → list all iterations
        POST /saved-prompts/{id}/iterations/  → create a new iteration

        Bridges SavedPrompt → PromptHistory → PromptIteration by
        auto-creating a PromptHistory entry the first time and caching its
        id in saved_prompt.metadata['history_id'].
        """
        saved_prompt = self.get_object()

        # ── GET ──────────────────────────────────────────────────────────────
        if request.method == 'GET':
            history_id = (saved_prompt.metadata or {}).get('history_id')
            if not history_id:
                return Response({'iterations': [], 'count': 0})
            try:
                history = PromptHistory.objects.get(id=history_id, user=request.user)
            except PromptHistory.DoesNotExist:
                return Response({'iterations': [], 'count': 0})

            qs = PromptIteration.objects.filter(
                parent_prompt=history, is_deleted=False
            ).order_by('iteration_number')
            serializer = PromptIterationSerializer(qs, many=True)
            return Response({'iterations': serializer.data, 'count': qs.count()})

        # ── POST ─────────────────────────────────────────────────────────────
        # Get or create the PromptHistory anchor for this saved prompt
        history_id = (saved_prompt.metadata or {}).get('history_id')
        history = None
        if history_id:
            try:
                history = PromptHistory.objects.get(id=history_id, user=request.user)
            except PromptHistory.DoesNotExist:
                history = None

        if not history:
            history = PromptHistory.objects.create(
                user=request.user,
                original_prompt=saved_prompt.content,
                source='saved_prompt',
                meta={'saved_prompt_id': str(saved_prompt.id)},
            )
            metadata = saved_prompt.metadata or {}
            metadata['history_id'] = str(history.id)
            saved_prompt.metadata = metadata
            saved_prompt.save(update_fields=['metadata', 'updated_at'])

        # Inject parent_prompt so the serializer doesn't need it from the client
        data = {**request.data, 'parent_prompt': str(history.id)}

        serializer = PromptIterationCreateSerializer(
            data=data, context={'request': request}
        )
        if serializer.is_valid():
            iteration = serializer.save()
            return Response(
                PromptIterationSerializer(iteration).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== PromptIteration ViewSet ====================

@extend_schema_view(
    list=extend_schema(
        summary="List prompt iterations",
        description="Get all prompt iterations for the authenticated user.",
        tags=['Prompt Iterations']
    ),
    create=extend_schema(
        summary="Create prompt iteration",
        description="Create a new iteration for a prompt.",
        tags=['Prompt Iterations']
    ),
    retrieve=extend_schema(
        summary="Get prompt iteration",
        description="Retrieve a specific prompt iteration by ID.",
        tags=['Prompt Iterations']
    ),
    update=extend_schema(
        summary="Update prompt iteration",
        description="Update an existing prompt iteration.",
        tags=['Prompt Iterations']
    ),
    partial_update=extend_schema(
        summary="Partial update prompt iteration",
        description="Partially update an existing prompt iteration.",
        tags=['Prompt Iterations']
    ),
    destroy=extend_schema(
        summary="Delete prompt iteration",
        description="Soft-delete a prompt iteration.",
        tags=['Prompt Iterations']
    ),
)
class PromptIterationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing prompt iterations.
    
    Tracks versions and iterations of prompts for version control
    and AI interaction history.
    
    **Also available via GraphQL at `/api/graphql/`**
    """
    queryset = PromptIteration.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent_prompt', 'interaction_type', 'is_bookmarked', 'is_active']
    search_fields = ['prompt_text', 'ai_response', 'feedback_notes']
    ordering_fields = ['created_at', 'iteration_number', 'user_rating']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = PromptIteration.objects.filter(is_deleted=False)
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return PromptIterationCreateSerializer
        return PromptIterationSerializer

    def perform_destroy(self, instance):
        instance.soft_delete()

    @extend_schema(
        summary="Set as active iteration",
        description="Mark this iteration as the active version.",
        responses={200: PromptIterationSerializer},
        tags=['Prompt Iterations']
    )
    @action(detail=True, methods=['post'], url_path='set-active')
    def set_active(self, request, pk=None):
        """Set this iteration as the active version"""
        instance = self.get_object()
        instance.set_as_active()
        serializer = PromptIterationSerializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Toggle bookmark",
        description="Toggle bookmark status of an iteration.",
        responses={200: PromptIterationSerializer},
        tags=['Prompt Iterations']
    )
    @action(detail=True, methods=['post'], url_path='toggle-bookmark')
    def toggle_bookmark(self, request, pk=None):
        """Toggle bookmark status"""
        instance = self.get_object()
        instance.is_bookmarked = not instance.is_bookmarked
        instance.save(update_fields=['is_bookmarked'])
        return Response({
            'id': str(instance.id),
            'is_bookmarked': instance.is_bookmarked,
            'message': f"Iteration {'bookmarked' if instance.is_bookmarked else 'unbookmarked'}"
        })

    @extend_schema(
        summary="Get bookmarked iterations",
        description="Get all bookmarked iterations.",
        responses={200: PromptIterationSerializer(many=True)},
        tags=['Prompt Iterations']
    )
    @action(detail=False, methods=['get'], url_path='bookmarked')
    def bookmarked(self, request):
        """Get all bookmarked iterations"""
        queryset = self.get_queryset().filter(is_bookmarked=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PromptIterationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PromptIterationSerializer(queryset, many=True)
        return Response(serializer.data)


# ==================== ConversationThread ViewSet ====================

@extend_schema_view(
    list=extend_schema(
        summary="List conversation threads",
        description="Get all conversation threads for the authenticated user.",
        tags=['Conversation Threads']
    ),
    create=extend_schema(
        summary="Create conversation thread",
        description="Create a new conversation thread.",
        tags=['Conversation Threads']
    ),
    retrieve=extend_schema(
        summary="Get conversation thread",
        description="Retrieve a specific conversation thread by ID.",
        tags=['Conversation Threads']
    ),
    update=extend_schema(
        summary="Update conversation thread",
        description="Update an existing conversation thread.",
        tags=['Conversation Threads']
    ),
    partial_update=extend_schema(
        summary="Partial update conversation thread",
        description="Partially update an existing conversation thread.",
        tags=['Conversation Threads']
    ),
    destroy=extend_schema(
        summary="Delete conversation thread",
        description="Soft-delete a conversation thread.",
        tags=['Conversation Threads']
    ),
)
class ConversationThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversation threads.
    
    Groups prompt iterations into conversation threads for multi-turn
    AI interactions with full history.
    
    **Also available via GraphQL at `/api/graphql/`**
    """
    queryset = ConversationThread.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'is_shared']
    ordering_fields = ['created_at', 'last_activity_at', 'total_iterations']
    ordering = ['-last_activity_at']

    def get_queryset(self):
        qs = ConversationThread.objects.filter(is_deleted=False)
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationThreadCreateSerializer
        return ConversationThreadSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])

    @extend_schema(
        summary="Add iteration to thread",
        description="Add an existing iteration to a conversation thread.",
        request={'application/json': {'type': 'object', 'properties': {'iteration_id': {'type': 'string', 'format': 'uuid'}}}},
        responses={200: ConversationThreadSerializer},
        tags=['Conversation Threads']
    )
    @action(detail=True, methods=['post'], url_path='add-iteration')
    def add_iteration(self, request, pk=None):
        """Add an iteration to this conversation thread"""
        thread = self.get_object()
        iteration_id = request.data.get('iteration_id')
        
        if not iteration_id:
            return Response({'error': 'iteration_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            iteration = PromptIteration.objects.get(
                id=iteration_id,
                user=request.user,
                is_deleted=False
            )
        except PromptIteration.DoesNotExist:
            return Response({'error': 'Iteration not found'}, status=status.HTTP_404_NOT_FOUND)
        
        thread.add_iteration(iteration)
        serializer = ConversationThreadSerializer(thread)
        return Response(serializer.data)