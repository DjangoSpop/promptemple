from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import PromptHistory
from .serializers import (
    PromptHistorySerializer, PromptHistoryCreateSerializer, PromptHistoryUpdateSerializer
)
from apps.prompt_history.services.optimization import enhance_prompt
from django.conf import settings
import logging

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
