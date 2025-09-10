"""
Chat app URL configuration
SSE streaming endpoints for real-time chat with template extraction
"""
from django.urls import path
from . import views
from .enhanced_views import (
    EnhancedChatCompletionsProxyView, 
    TemplateExtractionStatusView,
    ExtractedTemplatesView,
    ChatSessionsView
)

urlpatterns = [
    # Enhanced SSE Chat Completions endpoint with template extraction
    path('completions/', EnhancedChatCompletionsProxyView.as_view(), name='enhanced-chat-completions'),
    
    # Original endpoint (for backward compatibility)
    path('completions/basic/', views.ChatCompletionsProxyView.as_view(), name='chat-completions'),
    
    # Template extraction endpoints
    path('templates/status/', TemplateExtractionStatusView.as_view(), name='template-extraction-status'),
    path('templates/extracted/', ExtractedTemplatesView.as_view(), name='extracted-templates'),
    path('templates/extracted/<uuid:template_id>/', ExtractedTemplatesView.as_view(), name='extracted-template-detail'),
    
    # Chat session management
    path('sessions/', ChatSessionsView.as_view(), name='chat-sessions'),
    
    # Health check
    path('health/', views.ChatHealthView.as_view(), name='chat-health'),
    
    # Authentication test endpoint
    path('auth-test/', views.AuthTestView.as_view(), name='auth-test'),
]