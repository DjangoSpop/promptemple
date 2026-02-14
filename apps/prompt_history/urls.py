from rest_framework.routers import DefaultRouter
from .views import (
    PromptHistoryViewSet, 
    SavedPromptViewSet, 
    PromptIterationViewSet, 
    ConversationThreadViewSet
)

router = DefaultRouter()
router.register(r'history', PromptHistoryViewSet, basename='history')
router.register(r'saved-prompts', SavedPromptViewSet, basename='saved-prompts')
router.register(r'iterations', PromptIterationViewSet, basename='iterations')
router.register(r'threads', ConversationThreadViewSet, basename='threads')

urlpatterns = router.urls
