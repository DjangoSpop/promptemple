"""
RAG URL patterns
"""

from django.urls import path
from . import views

urlpatterns = [
    path('optimize/', views.rag_optimize, name='rag-optimize'),
    path('status/', views.rag_status_view, name='rag-status'),
]