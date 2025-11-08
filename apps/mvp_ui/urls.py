"""
URL Configuration for MVP UI
"""
from django.urls import path
from . import views

app_name = 'mvp_ui'

urlpatterns = [
    # Dashboard & Health
    path('', views.dashboard, name='dashboard'),
    path('health/', views.health_check, name='health_check'),
    path('metrics/', views.metrics, name='metrics'),
    
    # Authentication
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/profile/', views.profile_view, name='profile'),
    
    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<uuid:template_id>/', views.template_detail, name='template_detail'),
    path('templates/<uuid:template_id>/edit/', views.template_edit, name='template_edit'),
    path('templates/<uuid:template_id>/delete/', views.template_delete, name='template_delete'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:category_id>/', views.category_detail, name='category_detail'),
    
    # Research
    path('research/', views.research_list, name='research_list'),
    path('research/create/', views.research_create, name='research_create'),
    path('research/<uuid:job_id>/', views.research_detail, name='research_detail'),
    
    # SSE Demo
    path('sse/demo/', views.sse_demo, name='sse_demo'),
    path('sse/test/', views.sse_test, name='sse_test'),
    
    # AI Services
    path('ai/providers/', views.ai_providers, name='ai_providers'),
    path('ai/chat/', views.ai_chat, name='ai_chat'),
]
