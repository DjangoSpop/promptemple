from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

urlpatterns = [
    # Gamification endpoints
    path('achievements/', views.AchievementListView.as_view(), name='achievements'),
    path('badges/', views.BadgeListView.as_view(), name='badges'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('daily-challenges/', views.DailyChallengeView.as_view(), name='daily-challenges'),
    path('user-level/', views.UserLevelView.as_view(), name='user-level'),
    path('streak/', views.StreakView.as_view(), name='streak'),
    
    # Include router URLs
    path('', include(router.urls)),
]