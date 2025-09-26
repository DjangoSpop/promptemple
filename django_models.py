# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class User(AbstractUser):
    """Enhanced User model with gamification features"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)

    # Gamification fields
    credits = models.IntegerField(default=100)
    level = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    experience_points = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    daily_streak = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    last_login_date = models.DateField(null=True, blank=True)

    # User rank and status
    user_rank = models.CharField(max_length=50, default="Prompt Novice")
    is_premium = models.BooleanField(default=False)
    premium_expires_at = models.DateTimeField(null=True, blank=True)

    # Preferences
    theme_preference = models.CharField(
        max_length=20,
        choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")],
        default="system",
    )
    language_preference = models.CharField(max_length=10, default="en")
    ai_assistance_enabled = models.BooleanField(default=True)
    analytics_enabled = models.BooleanField(default=True)

    # Stats
    templates_created = models.IntegerField(default=0)
    templates_completed = models.IntegerField(default=0)
    total_prompts_generated = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username

    @property
    def completion_rate(self):
        if self.templates_created == 0:
            return 0
        return round((self.templates_completed / self.templates_created) * 100, 2)


# apps/templates/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid
import json

User = get_user_model()


class FieldType(models.TextChoices):
    TEXT = "text", "Text"
    TEXTAREA = "textarea", "Textarea"
    DROPDOWN = "dropdown", "Dropdown"
    CHECKBOX = "checkbox", "Checkbox"
    RADIO = "radio", "Radio"
    NUMBER = "number", "Number"


class PromptField(models.Model):
    """Individual field in a template form"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=200)
    placeholder = models.CharField(max_length=500, blank=True)
    field_type = models.CharField(
        max_length=20, choices=FieldType.choices, default=FieldType.TEXT
    )
    is_required = models.BooleanField(default=False)
    default_value = models.TextField(blank=True)
    validation_pattern = models.CharField(max_length=500, blank=True)
    help_text = models.TextField(blank=True)

    # For dropdown/radio/checkbox options
    options = models.JSONField(default=list, blank=True)

    # Field ordering within template
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "prompt_fields"
        ordering = ["order"]

    def __str__(self):
        return self.label


class TemplateCategory(models.Model):
    """Template categories for organization"""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default="#6366F1")  # Hex color
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "template_categories"
        ordering = ["order", "name"]
        verbose_name_plural = "Template Categories"

    def __str__(self):
        return self.name


class Template(models.Model):
    """Enhanced template model with AI features"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        TemplateCategory, on_delete=models.CASCADE, related_name="templates"
    )
    template_content = models.TextField()

    # Relationships
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_templates"
    )
    fields = models.ManyToManyField(
        PromptField, through="TemplateField", related_name="templates"
    )

    # Metadata
    version = models.CharField(max_length=20, default="1.0.0")
    tags = models.JSONField(default=list, blank=True)

    # AI Features
    is_ai_generated = models.BooleanField(default=False)
    ai_confidence = models.FloatField(
        default=0.0, validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    extracted_keywords = models.JSONField(default=list, blank=True)
    smart_suggestions = models.JSONField(default=dict, blank=True)

    # Advanced AI Framework fields
    prompt_framework = models.CharField(max_length=100, blank=True)
    subcategory = models.CharField(max_length=100, blank=True)
    use_cases = models.JSONField(default=list, blank=True)
    performance_metrics = models.JSONField(default=dict, blank=True)

    # Collaboration
    collaborators = models.ManyToManyField(
        User, blank=True, related_name="collaborated_templates"
    )

    # Analytics
    usage_count = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0.0)
    average_rating = models.FloatField(default=0.0)
    popularity_score = models.FloatField(default=0.0)

    # Status
    is_public = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Localization
    localizations = models.JSONField(default=dict, blank=True)

    # Related templates
    related_templates = models.ManyToManyField("self", blank=True, symmetrical=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "templates"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "is_public", "is_active"]),
            models.Index(fields=["author", "created_at"]),
            models.Index(fields=["popularity_score"]),
        ]

    def __str__(self):
        return self.title

    @property
    def field_count(self):
        return self.fields.count()


class TemplateField(models.Model):
    """Through model for Template-PromptField relationship with ordering"""

    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    field = models.ForeignKey(PromptField, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "template_fields"
        ordering = ["order"]
        unique_together = ["template", "field"]


class TemplateVersion(models.Model):
    """Version history for templates"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        Template, on_delete=models.CASCADE, related_name="version_history"
    )
    version = models.CharField(max_length=20)
    content_snapshot = models.JSONField()  # Full template data at this version
    changes_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "template_versions"
        ordering = ["-created_at"]
        unique_together = ["template", "version"]


class TemplateUsage(models.Model):
    """Track template usage for analytics"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        Template, on_delete=models.CASCADE, related_name="usage_logs"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="template_usage"
    )

    # Usage details
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    was_completed = models.BooleanField(default=False)
    time_spent_seconds = models.PositiveIntegerField(null=True, blank=True)

    # User inputs (for analytics, anonymized)
    field_completion_data = models.JSONField(default=dict, blank=True)
    generated_prompt_length = models.PositiveIntegerField(null=True, blank=True)

    # Context
    device_type = models.CharField(max_length=20, blank=True)
    app_version = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "template_usage"
        indexes = [
            models.Index(fields=["template", "started_at"]),
            models.Index(fields=["user", "started_at"]),
        ]


class TemplateRating(models.Model):
    """User ratings for templates"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        Template, on_delete=models.CASCADE, related_name="ratings"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="template_ratings"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "template_ratings"
        unique_together = ["template", "user"]


# apps/gamification/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Achievement(models.Model):
    """Achievements that users can unlock"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default="emoji_events")

    # Requirements
    requirement_type = models.CharField(
        max_length=50
    )  # e.g., 'templates_created', 'streak_days'
    requirement_value = models.IntegerField()

    # Rewards
    credits_reward = models.IntegerField(default=0)
    experience_reward = models.IntegerField(default=0)

    # Metadata
    category = models.CharField(max_length=50, blank=True)
    rarity = models.CharField(
        max_length=20,
        choices=[
            ("common", "Common"),
            ("rare", "Rare"),
            ("epic", "Epic"),
            ("legendary", "Legendary"),
        ],
        default="common",
    )
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False)  # Hidden until unlocked

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "achievements"

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Achievements unlocked by users"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="achievements"
    )
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    # Progress tracking
    progress_value = models.IntegerField(default=0)
    is_claimed = models.BooleanField(default=False)
    claimed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_achievements"
        unique_together = ["user", "achievement"]


class DailyChallenge(models.Model):
    """Daily challenges for users"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Challenge requirements
    challenge_type = models.CharField(
        max_length=50
    )  # e.g., 'complete_templates', 'use_ai_assistant'
    target_value = models.IntegerField()

    # Rewards
    credits_reward = models.IntegerField(default=50)
    experience_reward = models.IntegerField(default=25)

    # Timing
    date = models.DateField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "daily_challenges"
        unique_together = ["date", "challenge_type"]


class UserDailyChallenge(models.Model):
    """User progress on daily challenges"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="daily_challenges"
    )
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE)

    progress_value = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_daily_challenges"
        unique_together = ["user", "challenge"]


class CreditTransaction(models.Model):
    """Credit transaction history"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="credit_transactions"
    )

    amount = models.IntegerField()  # Positive for earning, negative for spending
    transaction_type = models.CharField(
        max_length=50,
        choices=[
            ("earned_ad", "Earned from Ad"),
            ("earned_achievement", "Earned from Achievement"),
            ("earned_challenge", "Earned from Challenge"),
            ("spent_ai", "Spent on AI Features"),
            ("spent_premium", "Spent on Premium Features"),
            ("bonus", "Bonus Credits"),
            ("refund", "Refund"),
        ],
    )
    description = models.CharField(max_length=200)

    # Related objects
    related_object_type = models.CharField(
        max_length=50, blank=True
    )  # e.g., 'achievement', 'template'
    related_object_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "credit_transactions"
        ordering = ["-created_at"]


# apps/analytics/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class AnalyticsEvent(models.Model):
    """Analytics events tracking"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="analytics_events",
    )

    # Event details
    event_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, default="general")
    properties = models.JSONField(default=dict, blank=True)

    # Session tracking
    session_id = models.CharField(max_length=100, blank=True)

    # Device/Context info
    device_info = models.JSONField(default=dict, blank=True)
    app_version = models.CharField(max_length=20, blank=True)
    platform = models.CharField(max_length=20, blank=True)

    # Geographic (if available)
    country_code = models.CharField(max_length=2, blank=True)
    timezone = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_events"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["event_name", "created_at"]),
            models.Index(fields=["category", "created_at"]),
        ]


class UserSession(models.Model):
    """User session tracking"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="sessions"
    )

    start_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    end_time = models.DateTimeField(null=True, blank=True)

    # Session metrics
    event_count = models.IntegerField(default=0)
    duration_seconds = models.IntegerField(null=True, blank=True)

    # Device info
    device_info = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "user_sessions"


class PerformanceMetric(models.Model):
    """App performance metrics"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_name = models.CharField(max_length=100)
    value = models.FloatField()
    unit = models.CharField(max_length=20)

    # Context
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)

    # Additional data
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "performance_metrics"
        indexes = [
            models.Index(fields=["metric_name", "created_at"]),
        ]


# apps/ai_services/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class AIInsight(models.Model):
    """AI-generated insights and suggestions"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_insights",
    )

    # Insight details
    insight_type = models.CharField(
        max_length=50,
        choices=[
            ("suggestion", "Suggestion"),
            ("warning", "Warning"),
            ("recommendation", "Recommendation"),
            ("optimization", "Optimization"),
        ],
    )
    title = models.CharField(max_length=200)
    description = models.TextField()

    # AI metadata
    confidence = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    ai_model = models.CharField(max_length=50, blank=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)

    # Related objects
    related_template = models.ForeignKey(
        "templates.Template", on_delete=models.CASCADE, null=True, blank=True
    )
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)

    # User interaction
    is_viewed = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    user_feedback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "ai_insights"
        ordering = ["-created_at"]


class AIInteraction(models.Model):
    """Track AI service interactions"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="ai_interactions"
    )

    # Interaction details
    interaction_type = models.CharField(
        max_length=50
    )  # e.g., 'template_optimization', 'content_analysis'
    ai_service = models.CharField(max_length=50)  # e.g., 'openai', 'anthropic'

    # Request/Response
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)

    # Performance
    response_time_ms = models.IntegerField(null=True, blank=True)
    was_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    # Cost tracking
    tokens_used = models.IntegerField(null=True, blank=True)
    estimated_cost = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_interactions"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["interaction_type", "created_at"]),
        ]


class PersonalizedRecommendation(models.Model):
    """Personalized template recommendations"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recommendations"
    )
    template = models.ForeignKey("templates.Template", on_delete=models.CASCADE)

    # Recommendation details
    confidence = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    reasoning = models.TextField()
    estimated_completion_time = models.IntegerField()  # in minutes
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ("simple", "Simple"),
            ("medium", "Medium"),
            ("complex", "Complex"),
        ],
    )

    # User interaction
    is_viewed = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "personalized_recommendations"
        unique_together = ["user", "template"]
        ordering = ["-confidence", "-created_at"]
