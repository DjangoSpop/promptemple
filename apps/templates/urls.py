from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.templates.views import TemplateCategoryViewSet, TemplateViewSet

router = DefaultRouter()
router.register(r'template-categories', TemplateCategoryViewSet, basename='template-categories')
router.register(r'templates', TemplateViewSet, basename='templates')

urlpatterns = [
    path('', include(router.urls)),
]