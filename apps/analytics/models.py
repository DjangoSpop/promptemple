
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()

# Import AI models from ai_services app
from apps.ai_services.models import AIProvider, AIModel


class ABTestExperiment(models.Model):
    """A/B testing experiments"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    # Experiment configuration
    variants = models.JSONField(default=list)  # List of variant configurations
    traffic_allocation = models.JSONField(default=dict)  # Percentage allocation per variant
    
    # Targeting
    target_audience = models.JSONField(default=dict, blank=True)
    exclusion_criteria = models.JSONField(default=dict, blank=True)
    
    # Status and timing
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Results tracking
    primary_metric = models.CharField(max_length=100)
    secondary_metrics = models.JSONField(default=list, blank=True)
    statistical_significance = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ab_test_experiments'

    def __str__(self):
        return self.name


class ABTestAssignment(models.Model):
    """User assignments to A/B test variants"""
    experiment = models.ForeignKey(ABTestExperiment, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ab_test_assignments')
    variant = models.CharField(max_length=50)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    # Outcome tracking
    converted = models.BooleanField(default=False)
    conversion_value = models.FloatField(null=True, blank=True)
    events_data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'ab_test_assignments'
        unique_together = ['experiment', 'user']

    def __str__(self):
        return f"{self.user.username} -> {self.experiment.name} ({self.variant})"


# Additional Domain Models for Complete Implementation

# apps/core/models.py
from django.db import models
import uuid

class AppConfiguration(models.Model):
    """Global app configuration"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
        ],
        default='string'
    )
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)  # Can be exposed to frontend
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'app_configurations'

    def __str__(self):
        return f"{self.key}: {self.value}"

    def get_typed_value(self):
        """Return value in correct Python type"""
        if self.data_type == 'integer':
            return int(self.value)
        elif self.data_type == 'float':
            return float(self.value)
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.data_type == 'json':
            import json
            return json.loads(self.value)
        return self.value


class SystemNotification(models.Model):
    """System-wide notifications and announcements"""
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
        ('feature', 'New Feature'),
        ('promotion', 'Promotion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    # Targeting
    target_all_users = models.BooleanField(default=True)
    target_user_groups = models.JSONField(default=list, blank=True)  # ['premium', 'new_users']
    target_platforms = models.JSONField(default=list, blank=True)  # ['ios', 'android', 'web']
    
    # Display settings
    is_dismissible = models.BooleanField(default=True)
    auto_dismiss_after_seconds = models.IntegerField(null=True, blank=True)
    show_on_pages = models.JSONField(default=list, blank=True)  # Specific pages to show on
    
    # Scheduling
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    dismiss_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_notifications'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class UserNotificationStatus(models.Model):
    """Track user interaction with notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_statuses')
    notification = models.ForeignKey(SystemNotification, on_delete=models.CASCADE, related_name='user_statuses')
    
    is_viewed = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    
    viewed_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user_notification_statuses'
        unique_together = ['user', 'notification']


# apps/templates/models.py - Additional Template Models
class TemplateCollaborationRequest(models.Model):
    """Collaboration requests for templates"""
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey('templates.Template', on_delete=models.CASCADE, related_name='collaboration_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collaboration_requests_sent')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collaboration_requests_received')
    
    message = models.TextField(blank=True)
    permissions = models.JSONField(default=list)  # ['view', 'edit', 'share']
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'template_collaboration_requests'
        unique_together = ['template', 'invited_user']


class TemplateFork(models.Model):
    """Track template forks/derivatives"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_template = models.ForeignKey('templates.Template', on_delete=models.CASCADE, related_name='forks')
    forked_template = models.ForeignKey('templates.Template', on_delete=models.CASCADE, related_name='fork_source')
    forked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='template_forks')
    
    fork_reason = models.TextField(blank=True)
    changes_summary = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'template_forks'


class TemplateReport(models.Model):
    """User reports for inappropriate templates"""
    REPORT_REASONS = [
        ('inappropriate_content', 'Inappropriate Content'),
        ('spam', 'Spam'),
        ('copyright_violation', 'Copyright Violation'),
        ('misleading', 'Misleading'),
        ('low_quality', 'Low Quality'),
        ('other', 'Other'),
    ]
    
    REPORT_STATUS = [
        ('pending', 'Pending'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey('templates.Template', on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='template_reports')
    
    reason = models.CharField(max_length=50, choices=REPORT_REASONS)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='pending')
    
    # Moderation
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'template_reports'
        unique_together = ['template', 'reporter']


# apps/gamification/models.py - Additional Gamification Models
class Badge(models.Model):
    """Collectible badges for users"""
    BADGE_RARITIES = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
        ('mythic', 'Mythic'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#6366F1')  # Hex color
    
    rarity = models.CharField(max_length=20, choices=BADGE_RARITIES, default='common')
    category = models.CharField(max_length=50, blank=True)
    
    # Unlock criteria
    unlock_criteria = models.JSONField(default=dict)
    is_secret = models.BooleanField(default=False)  # Hidden until unlocked
    
    # Metadata
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'badges'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Badges earned by users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='earned_by')
    
    earned_at = models.DateTimeField(auto_now_add=True)
    showcase = models.BooleanField(default=False)  # Display on profile
    
    # Context of earning
    earned_for = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'user_badges'
        unique_together = ['user', 'badge']


class Leaderboard(models.Model):
    """Dynamic leaderboards"""
    LEADERBOARD_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('all_time', 'All Time'),
        ('seasonal', 'Seasonal'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    leaderboard_type = models.CharField(max_length=20, choices=LEADERBOARD_TYPES)
    
    # Metrics
    metric_name = models.CharField(max_length=100)  # 'templates_created', 'credits_earned', etc.
    metric_display_name = models.CharField(max_length=100)
    
    # Configuration
    max_entries = models.IntegerField(default=100)
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'leaderboards'

    def __str__(self):
        return f"{self.name} ({self.leaderboard_type})"


class LeaderboardEntry(models.Model):
    """Individual leaderboard entries"""
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name='entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    
    rank = models.IntegerField()
    score = models.FloatField()
    previous_rank = models.IntegerField(null=True, blank=True)
    
    # Metadata
    additional_data = models.JSONField(default=dict, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leaderboard_entries'
        unique_together = ['leaderboard', 'user']
        ordering = ['rank']


class StreakTracker(models.Model):
    """Track various user streaks"""
    STREAK_TYPES = [
        ('daily_login', 'Daily Login'),
        ('template_creation', 'Template Creation'),
        ('ai_usage', 'AI Usage'),
        ('achievement_unlock', 'Achievement Unlock'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streaks')
    streak_type = models.CharField(max_length=50, choices=STREAK_TYPES)
    
    current_streak = models.IntegerField(default=0)
    best_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField()
    
    # Milestones
    milestone_rewards_claimed = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'streak_trackers'
        unique_together = ['user', 'streak_type']


# apps/ai_services/models.py - Additional AI Models  
class AIPromptTemplate(models.Model):
    """Pre-built AI prompt templates"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    prompt_template = models.TextField()
    
    # Configuration
    ai_provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, related_name='prompt_templates')
    recommended_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='prompt_templates')
    
    # Parameters
    default_parameters = models.JSONField(default=dict)
    parameter_schema = models.JSONField(default=dict)  # JSON schema for validation
    
    # Usage and quality
    usage_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_prompt_templates'

    def __str__(self):
        return self.name


class MLModelPrediction(models.Model):
    """Store ML model predictions for analysis"""
    model_name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=50)
    
    # Input and output
    input_data = models.JSONField()
    prediction = models.JSONField()
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    # Context
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)
    
    # Quality tracking
    actual_outcome = models.JSONField(null=True, blank=True)  # For accuracy measurement
    feedback_score = models.IntegerField(null=True, blank=True)  # User feedback
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ml_model_predictions'
        indexes = [
            models.Index(fields=['model_name', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]