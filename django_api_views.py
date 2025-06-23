# apps/templates/serializers.py
from rest_framework import serializers
from .models import (
    Template,
    PromptField,
    TemplateCategory,
    TemplateUsage,
    TemplateRating,
)
from apps.users.serializers import UserSerializer


class PromptFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptField
        fields = [
            "id",
            "label",
            "placeholder",
            "field_type",
            "is_required",
            "default_value",
            "validation_pattern",
            "help_text",
            "options",
            "order",
        ]


class TemplateCategorySerializer(serializers.ModelSerializer):
    template_count = serializers.SerializerMethodField()

    class Meta:
        model = TemplateCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "color",
            "is_active",
            "order",
            "template_count",
        ]

    def get_template_count(self, obj):
        return obj.templates.filter(is_active=True, is_public=True).count()


class TemplateListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = TemplateCategorySerializer(read_only=True)
    field_count = serializers.ReadOnlyField()

    class Meta:
        model = Template
        fields = [
            "id",
            "title",
            "description",
            "category",
            "author",
            "version",
            "tags",
            "usage_count",
            "completion_rate",
            "average_rating",
            "popularity_score",
            "is_featured",
            "field_count",
            "created_at",
            "updated_at",
        ]


class TemplateDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = TemplateCategorySerializer(read_only=True)
    fields = PromptFieldSerializer(many=True, read_only=True)
    field_count = serializers.ReadOnlyField()

    class Meta:
        model = Template
        fields = [
            "id",
            "title",
            "description",
            "category",
            "template_content",
            "author",
            "fields",
            "version",
            "tags",
            "is_ai_generated",
            "ai_confidence",
            "extracted_keywords",
            "smart_suggestions",
            "usage_count",
            "completion_rate",
            "average_rating",
            "popularity_score",
            "is_public",
            "is_featured",
            "field_count",
            "localizations",
            "created_at",
            "updated_at",
        ]


class TemplateCreateUpdateSerializer(serializers.ModelSerializer):
    fields_data = PromptFieldSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Template
        fields = [
            "title",
            "description",
            "category",
            "template_content",
            "version",
            "tags",
            "is_public",
            "fields_data",
        ]

    def create(self, validated_data):
        fields_data = validated_data.pop("fields_data", [])
        validated_data["author"] = self.context["request"].user
        template = Template.objects.create(**validated_data)

        # Create and associate fields
        for order, field_data in enumerate(fields_data):
            field_data["order"] = order
            field = PromptField.objects.create(**field_data)
            template.fields.add(field)

        return template

    def update(self, instance, validated_data):
        fields_data = validated_data.pop("fields_data", None)

        # Update template fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update fields if provided
        if fields_data is not None:
            # Remove existing fields
            instance.fields.clear()

            # Add new fields
            for order, field_data in enumerate(fields_data):
                field_data["order"] = order
                field = PromptField.objects.create(**field_data)
                instance.fields.add(field)

        return instance


class TemplateUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateUsage
        fields = [
            "id",
            "template",
            "started_at",
            "completed_at",
            "was_completed",
            "time_spent_seconds",
            "device_type",
            "app_version",
        ]
        read_only_fields = ["id", "started_at"]


class TemplateRatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TemplateRating
        fields = ["id", "user", "rating", "review", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


# apps/templates/views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from .models import Template, TemplateCategory, TemplateUsage, TemplateRating
from .serializers import (
    TemplateListSerializer,
    TemplateDetailSerializer,
    TemplateCreateUpdateSerializer,
    TemplateCategorySerializer,
    TemplateUsageSerializer,
    TemplateRatingSerializer,
)
from apps.analytics.services import AnalyticsService
from apps.ai_services.services import AIService


class TemplateCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TemplateCategory.objects.filter(is_active=True)
    serializer_class = TemplateCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class TemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "is_featured", "is_public"]
    search_fields = ["title", "description", "tags"]
    ordering_fields = [
        "created_at",
        "updated_at",
        "popularity_score",
        "usage_count",
        "average_rating",
    ]
    ordering = ["-popularity_score", "-created_at"]

    def get_queryset(self):
        queryset = Template.objects.filter(is_active=True)

        if self.action == "list":
            # Only show public templates for list view, unless user is viewing their own
            if self.request.query_params.get("my_templates"):
                queryset = queryset.filter(author=self.request.user)
            else:
                queryset = queryset.filter(is_public=True)

        return queryset.select_related("author", "category").prefetch_related("fields")

    def get_serializer_class(self):
        if self.action == "list":
            return TemplateListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return TemplateCreateUpdateSerializer
        return TemplateDetailSerializer

    def perform_create(self, serializer):
        template = serializer.save(author=self.request.user)

        # Track analytics
        AnalyticsService.track_event(
            user=self.request.user,
            event_name="template_created",
            properties={"template_id": str(template.id), "title": template.title},
        )

    @action(detail=True, methods=["post"])
    def use_template(self, request, pk=None):
        """Start using a template"""
        template = self.get_object()

        # Create usage record
        usage = TemplateUsage.objects.create(
            template=template,
            user=request.user,
            device_type=request.data.get("device_type", ""),
            app_version=request.data.get("app_version", ""),
        )

        # Update template usage count
        template.usage_count += 1
        template.save(update_fields=["usage_count"])

        # Track analytics
        AnalyticsService.track_event(
            user=request.user,
            event_name="template_started",
            properties={"template_id": str(template.id)},
        )

        return Response({"usage_id": usage.id, "message": "Template usage started"})

    @action(detail=True, methods=["post"])
    def complete_template(self, request, pk=None):
        """Mark template usage as completed"""
        template = self.get_object()
        usage_id = request.data.get("usage_id")

        try:
            usage = TemplateUsage.objects.get(
                id=usage_id, template=template, user=request.user, was_completed=False
            )

            usage.was_completed = True
            usage.completed_at = timezone.now()
            usage.time_spent_seconds = request.data.get("time_spent_seconds")
            usage.generated_prompt_length = request.data.get("prompt_length")
            usage.save()

            # Update user stats
            user = request.user
            user.templates_completed += 1
            user.total_prompts_generated += 1
            user.save(update_fields=["templates_completed", "total_prompts_generated"])

            # Award credits
            from apps.gamification.services import GamificationService

            GamificationService.award_credits(
                user=user, amount=10, reason=f"Completed template: {template.title}"
            )

            # Track analytics
            AnalyticsService.track_event(
                user=request.user,
                event_name="template_completed",
                properties={
                    "template_id": str(template.id),
                    "time_spent": usage.time_spent_seconds,
                    "prompt_length": usage.generated_prompt_length,
                },
            )

            return Response({"message": "Template completed successfully"})

        except TemplateUsage.DoesNotExist:
            return Response(
                {"error": "Usage record not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["post"])
    def rate_template(self, request, pk=None):
        """Rate and review a template"""
        template = self.get_object()

        rating_data = {
            "template": template.id,
            "rating": request.data.get("rating"),
            "review": request.data.get("review", ""),
        }

        # Update or create rating
        rating, created = TemplateRating.objects.update_or_create(
            template=template,
            user=request.user,
            defaults={"rating": rating_data["rating"], "review": rating_data["review"]},
        )

        # Update template average rating
        avg_rating = template.ratings.aggregate(avg=Avg("rating"))["avg"] or 0
        template.average_rating = round(avg_rating, 2)
        template.save(update_fields=["average_rating"])

        serializer = TemplateRatingSerializer(rating)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        """Get trending templates"""
        templates = Template.objects.filter(is_active=True, is_public=True).order_by(
            "-popularity_score", "-usage_count"
        )[:10]

        serializer = TemplateListSerializer(templates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get featured templates"""
        templates = Template.objects.filter(
            is_active=True, is_public=True, is_featured=True
        ).order_by("-created_at")[:5]

        serializer = TemplateListSerializer(templates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def my_templates(self, request):
        """Get user's templates"""
        templates = Template.objects.filter(
            author=request.user, is_active=True
        ).order_by("-created_at")

        serializer = TemplateListSerializer(templates, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def analyze_with_ai(self, request, pk=None):
        """Analyze template with AI for optimization suggestions"""
        template = self.get_object()

        if not request.user.ai_assistance_enabled:
            return Response(
                {"error": "AI assistance is disabled"}, status=status.HTTP_403_FORBIDDEN
            )

        # Use AI service to analyze template
        analysis = AIService.analyze_template(template, request.user)

        return Response(analysis)


# apps/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.gamification.models import UserAchievement, CreditTransaction

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "user_rank",
            "is_premium",
        ]
        read_only_fields = ["id", "user_rank", "is_premium"]


class UserProfileSerializer(serializers.ModelSerializer):
    completion_rate = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "credits",
            "level",
            "experience_points",
            "daily_streak",
            "user_rank",
            "is_premium",
            "premium_expires_at",
            "theme_preference",
            "language_preference",
            "ai_assistance_enabled",
            "analytics_enabled",
            "templates_created",
            "templates_completed",
            "total_prompts_generated",
            "completion_rate",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "credits",
            "level",
            "experience_points",
            "daily_streak",
            "user_rank",
            "is_premium",
            "premium_expires_at",
            "templates_created",
            "templates_completed",
            "total_prompts_generated",
            "completion_rate",
            "created_at",
        ]


class UserStatsSerializer(serializers.ModelSerializer):
    completion_rate = serializers.ReadOnlyField()
    recent_achievements = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "credits",
            "level",
            "experience_points",
            "daily_streak",
            "user_rank",
            "templates_created",
            "templates_completed",
            "total_prompts_generated",
            "completion_rate",
            "recent_achievements",
        ]

    def get_recent_achievements(self, obj):
        recent = UserAchievement.objects.filter(user=obj, is_claimed=True).order_by(
            "-unlocked_at"
        )[:3]
        return [
            {"name": ua.achievement.name, "unlocked_at": ua.unlocked_at}
            for ua in recent
        ]


# apps/users/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import UserProfileSerializer, UserStatsSerializer

User = get_user_model()


class UserViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=["get"])
    def profile(self, request):
        """Get user profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"])
    def update_profile(self, request):
        """Update user profile"""
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get user gamification stats"""
        serializer = UserStatsSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def update_daily_streak(self, request):
        """Update user's daily streak"""
        from apps.gamification.services import GamificationService

        updated_streak = GamificationService.update_daily_streak(request.user)

        return Response(
            {"daily_streak": updated_streak, "message": "Daily streak updated"}
        )


# apps/gamification/serializers.py
from rest_framework import serializers
from .models import (
    Achievement,
    UserAchievement,
    DailyChallenge,
    UserDailyChallenge,
    CreditTransaction,
)


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "category",
            "rarity",
            "credits_reward",
            "experience_reward",
            "requirement_type",
            "requirement_value",
        ]


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = [
            "id",
            "achievement",
            "progress_value",
            "is_claimed",
            "unlocked_at",
            "claimed_at",
        ]


class DailyChallengeSerializer(serializers.ModelSerializer):
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = DailyChallenge
        fields = [
            "id",
            "title",
            "description",
            "challenge_type",
            "target_value",
            "credits_reward",
            "experience_reward",
            "date",
            "user_progress",
        ]

    def get_user_progress(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                user_challenge = UserDailyChallenge.objects.get(
                    user=request.user, challenge=obj
                )
                return {
                    "progress_value": user_challenge.progress_value,
                    "is_completed": user_challenge.is_completed,
                    "completed_at": user_challenge.completed_at,
                }
            except UserDailyChallenge.DoesNotExist:
                return {
                    "progress_value": 0,
                    "is_completed": False,
                    "completed_at": None,
                }
        return None


class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = ["id", "amount", "transaction_type", "description", "created_at"]


# apps/gamification/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import (
    Achievement,
    UserAchievement,
    DailyChallenge,
    UserDailyChallenge,
    CreditTransaction,
)
from .serializers import (
    AchievementSerializer,
    UserAchievementSerializer,
    DailyChallengeSerializer,
    CreditTransactionSerializer,
)
from .services import GamificationService


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Achievement.objects.filter(is_active=True)
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def user_achievements(self, request):
        """Get user's achievements"""
        user_achievements = (
            UserAchievement.objects.filter(user=request.user)
            .select_related("achievement")
            .order_by("-unlocked_at")
        )

        serializer = UserAchievementSerializer(user_achievements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def claim_achievement(self, request, pk=None):
        """Claim an achievement reward"""
        try:
            user_achievement = UserAchievement.objects.get(
                achievement_id=pk, user=request.user, is_claimed=False
            )

            # Award credits and experience
            achievement = user_achievement.achievement
            user = request.user

            user.credits += achievement.credits_reward
            user.experience_points += achievement.experience_reward
            user.save()

            # Mark as claimed
            user_achievement.is_claimed = True
            user_achievement.claimed_at = timezone.now()
            user_achievement.save()

            # Create transaction record
            CreditTransaction.objects.create(
                user=user,
                amount=achievement.credits_reward,
                transaction_type="earned_achievement",
                description=f"Achievement claimed: {achievement.name}",
                related_object_type="achievement",
                related_object_id=str(achievement.id),
            )

            return Response(
                {
                    "message": "Achievement claimed successfully",
                    "credits_earned": achievement.credits_reward,
                    "experience_earned": achievement.experience_reward,
                }
            )

        except UserAchievement.DoesNotExist:
            return Response(
                {"error": "Achievement not found or already claimed"},
                status=status.HTTP_404_NOT_FOUND,
            )


class DailyChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DailyChallengeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        today = timezone.now().date()
        return DailyChallenge.objects.filter(date=today, is_active=True)


class CreditTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CreditTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CreditTransaction.objects.filter(user=self.request.user)


# promptcraft/urls.py - Main URL configuration
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API Authentication
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # API Routes
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/templates/", include("apps.templates.urls")),
    path("api/v1/gamification/", include("apps.gamification.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/ai/", include("apps.ai_services.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# apps/templates/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TemplateViewSet, TemplateCategoryViewSet

router = DefaultRouter()
router.register(r"categories", TemplateCategoryViewSet)
router.register(r"", TemplateViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

# apps/users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]

# apps/gamification/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AchievementViewSet, DailyChallengeViewSet, CreditTransactionViewSet

router = DefaultRouter()
router.register(r"achievements", AchievementViewSet)
router.register(r"daily-challenges", DailyChallengeViewSet, basename="dailychallenge")
router.register(r"transactions", CreditTransactionViewSet, basename="transaction")

urlpatterns = [
    path("", include(router.urls)),
]
