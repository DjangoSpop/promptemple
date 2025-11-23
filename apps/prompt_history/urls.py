from rest_framework.routers import DefaultRouter
from .views import PromptHistoryViewSet

router = DefaultRouter()
router.register(r'history', PromptHistoryViewSet, basename='history')

urlpatterns = router.urls
