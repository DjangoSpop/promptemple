from django.urls import path
from . import views

app_name = 'orchestrator'

urlpatterns = [
    # Intent detection endpoint
    path('intent/', views.IntentDetectionView.as_view(), name='intent-detection'),
    
    # Prompt assessment endpoint
    path('assess/', views.PromptAssessmentView.as_view(), name='prompt-assessment'),
    
    # Template rendering endpoint
    path('render/', views.TemplateRenderingView.as_view(), name='template-rendering'),
    
    # Library search endpoint
    path('search/', views.LibrarySearchView.as_view(), name='library-search'),
    
    # Get template endpoint
    path('template/<int:template_id>/', views.GetTemplateView.as_view(), name='get-template'),
    path('template/', views.GetTemplateView.as_view(), name='get-template-by-name'),
]
