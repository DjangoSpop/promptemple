from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.templates.views import TemplateCategoryViewSet , TemplateViewSet

router = DefaultRouter()
router.register(r'categories', TemplateCategoryViewSet)
router.register(r'', TemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]