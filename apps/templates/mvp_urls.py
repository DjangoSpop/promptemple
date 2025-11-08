"""
MVP Templates API URLs - Clean professional endpoints for template management

Provides essential template CRUD functionality:
- Template listing with search and pagination
- Template CRUD operations
- Category management
- Basic analytics
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import mvp_views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'', mvp_views.MVPTemplateViewSet, basename='template')
router.register(r'categories', mvp_views.MVPTemplateCategoryViewSet, basename='category')

app_name = 'mvp_templates'

urlpatterns = [
    # Template search and discovery
    path('search/', mvp_views.mvp_search_templates, name='search'),
    path('featured/', mvp_views.mvp_featured_templates, name='featured'),
    
    # System status
    path('status/', mvp_views.mvp_system_status, name='status'),
    
    # Include router URLs (templates CRUD, categories)
    path('', include(router.urls)),
]