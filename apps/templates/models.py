from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class FieldType(models.TextChoices):
    """Enum for different field types in templates"""
    TEXT = 'text', 'Text Input'
    TEXTAREA = 'textarea', 'Text Area' 
    DROPDOWN = 'dropdown', 'Dropdown Select'
    CHECKBOX = 'checkbox', 'Checkbox List'
    RADIO = 'radio', 'Radio Buttons'
    NUMBER = 'number', 'Number Input'

class TemplateCategory(models.Model):
    """Categories for organizing templates"""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Icon name for UI display"
    )
    color = models.CharField(
        max_length=7, 
        default='#6366F1',
        help_text="Hex color code for category"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in lists"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'template_categories'
        ordering = ['order', 'name']
        verbose_name_plural = 'Template Categories'

    def __str__(self):
        return self.name


class PromptField(models.Model):
    """Individual field configuration for templates"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(
        max_length=200,
        help_text="Display label for the field"
    )
    placeholder = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Placeholder text shown in input"
    )
    field_type = models.CharField(
        max_length=20, 
        choices=FieldType.choices, 
        default=FieldType.TEXT,
        help_text="Type of input field to display"
    )
    is_required = models.BooleanField(
        default=False,
        help_text="Whether this field is mandatory"
    )
    default_value = models.TextField(
        blank=True,
        help_text="Default value for the field"
    )
    validation_pattern = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Regex pattern for validation"
    )
    help_text = models.TextField(
        blank=True,
        help_text="Additional help text for users"
    )
    
    # For dropdown/radio/checkbox options
    options = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of options for choice fields"
    )
    
    # Field ordering within template
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within template"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prompt_fields'
        ordering = ['order']
        indexes = [
            models.Index(fields=['field_type']),
            models.Index(fields=['is_required']),
        ]

    def __str__(self):
        return self.label

    def clean(self):
        """Custom validation for field configuration"""
        from django.core.exceptions import ValidationError
        
        # Validate that choice fields have options
        if self.field_type in [FieldType.DROPDOWN, FieldType.RADIO, FieldType.CHECKBOX]:
            if not self.options or len(self.options) == 0:
                raise ValidationError(
                    f'{self.get_field_type_display()} fields must have options'
                )


class Template(models.Model):
    """Main template model with all features"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(
        max_length=200,
        help_text="Template title"
    )
    description = models.TextField(
        help_text="Description of what this template does"
    )
    category = models.ForeignKey(
        TemplateCategory, 
        on_delete=models.CASCADE, 
        related_name='templates',
        help_text="Template category"
    )
    template_content = models.TextField(
        help_text="Template content with {{placeholders}}"
    )
    
    # Relationships
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_templates',
        help_text="User who created this template"
    )
    fields = models.ManyToManyField(
        PromptField, 
        through='TemplateField', 
        related_name='templates',
        help_text="Form fields for this template"
    )
    
    # Metadata
    version = models.CharField(
        max_length=20, 
        default='1.0.0',
        help_text="Template version"
    )
    tags = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of tags for searching"
    )
    
    # AI Features
    is_ai_generated = models.BooleanField(
        default=False,
        help_text="Whether this template was generated by AI"
    )
    ai_confidence = models.FloatField(
        default=0.0, 
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="AI confidence score (0-1)"
    )
    extracted_keywords = models.JSONField(
        default=list, 
        blank=True,
        help_text="AI-extracted keywords"
    )
    smart_suggestions = models.JSONField(
        default=dict, 
        blank=True,
        help_text="AI-generated suggestions"
    )
    
    # Collaboration
    collaborators = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='collaborated_templates',
        help_text="Users who can edit this template"
    )
    
    # Analytics and metrics
    usage_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of times template was used"
    )
    completion_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Rate of successful completions (0-1)"
    )
    average_rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Average user rating (0-5 stars)"
    )
    popularity_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0)],
        help_text="Calculated popularity score"
    )
    
    # Status and visibility
    is_public = models.BooleanField(
        default=True,
        help_text="Whether template is publicly visible"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether template is featured"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether template is active"
    )
    
    # Localization support
    localizations = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Translations for different languages"
    )
    
    # Related templates for recommendations
    related_templates = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        help_text="Related template recommendations"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'templates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_public', 'is_active']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['popularity_score']),
            models.Index(fields=['is_featured', 'is_public']),
            models.Index(fields=['usage_count']),
        ]

    def __str__(self):
        return self.title

    @property
    def field_count(self):
        """Get number of fields in this template"""
        return self.fields.count()

    def update_popularity_score(self):
        """Calculate and update popularity score based on various metrics"""
        # Weighted calculation of popularity
        usage_weight = 0.4
        rating_weight = 0.3
        completion_weight = 0.2
        recency_weight = 0.1
        
        # Normalize usage count (assuming max of 1000 uses)
        usage_score = min(self.usage_count / 1000.0, 1.0)
        
        # Rating score (0-5 to 0-1)
        rating_score = self.average_rating / 5.0
        
        # Completion rate is already 0-1
        completion_score = self.completion_rate
        
        # Recency score based on creation date
        from django.utils import timezone
        days_old = (timezone.now() - self.created_at).days
        recency_score = max(0, 1 - (days_old / 365.0))  # Decay over a year
        
        self.popularity_score = (
            usage_score * usage_weight +
            rating_score * rating_weight +
            completion_score * completion_weight +
            recency_score * recency_weight
        ) * 100  # Scale to 0-100
        
        self.save(update_fields=['popularity_score'])


class TemplateField(models.Model):
    """Through model for Template-PromptField relationship with ordering"""
    
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    field = models.ForeignKey(PromptField, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'template_fields'
        ordering = ['order']
        unique_together = ['template', 'field']

    def __str__(self):
        return f"{self.template.title} - {self.field.label}"


class TemplateUsage(models.Model):
    """Track template usage sessions for analytics and gamification"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        Template, 
        on_delete=models.CASCADE,
        related_name='usage_logs'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='template_usages'
    )
    
    # Session tracking
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    was_completed = models.BooleanField(default=False)
    
    # Performance metrics
    time_spent_seconds = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Time spent in seconds completing the template"
    )
    generated_prompt_length = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Length of the final generated prompt"
    )
    
    # Field completion data
    field_completion_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON data showing which fields were completed and their values"
    )
    
    # Context information
    device_type = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Device type: mobile, tablet, desktop"
    )
    app_version = models.CharField(
        max_length=20, 
        blank=True,
        help_text="App version when template was used"
    )
    referrer_source = models.CharField(
        max_length=100, 
        blank=True,
        help_text="How user found this template"
    )
    
    # Quality metrics
    user_satisfaction = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="User satisfaction rating (1-5) given after completion"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'template_usage'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['template', 'user']),
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['template', 'was_completed']),
            models.Index(fields=['was_completed', 'completed_at']),
        ]

    def __str__(self):
        status = "Completed" if self.was_completed else "In Progress"
        return f"{self.user.username} - {self.template.title} ({status})"

    @property
    def duration_minutes(self):
        """Get duration in minutes"""
        if self.time_spent_seconds:
            return round(self.time_spent_seconds / 60, 1)
        return None

    @property
    def completion_rate_percentage(self):
        """Calculate completion rate for this usage session"""
        if not self.field_completion_data:
            return 0
        
        total_fields = self.template.field_count
        completed_fields = len([
            field for field, data in self.field_completion_data.items() 
            if data.get('completed', False)
        ])
        
        return (completed_fields / total_fields * 100) if total_fields > 0 else 0


class TemplateRating(models.Model):
    """User ratings and reviews for templates"""
    
    template = models.ForeignKey(
        Template, 
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='template_ratings'
    )
    
    # Rating and review
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    review = models.TextField(
        blank=True,
        max_length=1000,
        help_text="Optional written review"
    )
    
    # Detailed feedback categories
    ease_of_use = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How easy was the template to use?"
    )
    quality_of_output = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Quality of the generated prompt"
    )
    design_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Template design and layout rating"
    )
    
    # Recommendation
    would_recommend = models.BooleanField(
        null=True,
        blank=True,
        help_text="Would you recommend this template to others?"
    )
    
    # Helpfulness tracking
    helpful_votes = models.PositiveIntegerField(
        default=0,
        help_text="Number of users who found this review helpful"
    )
    total_votes = models.PositiveIntegerField(
        default=0,
        help_text="Total number of helpfulness votes"
    )
    
    # Moderation
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether this rating is from a verified template completion"
    )
    is_flagged = models.BooleanField(
        default=False,
        help_text="Whether this review has been flagged for review"
    )
    moderation_notes = models.TextField(
        blank=True,
        help_text="Internal moderation notes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'template_ratings'
        ordering = ['-created_at']
        unique_together = ['template', 'user']  # One rating per user per template
        indexes = [
            models.Index(fields=['template', 'rating']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['rating', 'created_at']),
            models.Index(fields=['is_verified', 'rating']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.template.title} ({self.rating}★)"

    @property
    def helpfulness_percentage(self):
        """Calculate helpfulness percentage"""
        if self.total_votes == 0:
            return None
        return round((self.helpful_votes / self.total_votes) * 100, 1)

    def save(self, *args, **kwargs):
        """Override save to update template average rating"""
        super().save(*args, **kwargs)
        
        # Update template's average rating
        from django.db.models import Avg
        avg_rating = self.template.ratings.aggregate(avg=Avg('rating'))['avg']
        if avg_rating:
            self.template.average_rating = round(avg_rating, 2)
            self.template.save(update_fields=['average_rating'])
            
            # Update popularity score
            self.template.update_popularity_score()


class TemplateBookmark(models.Model):
    """User bookmarks for templates"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='bookmarked_templates'
    )
    template = models.ForeignKey(
        Template, 
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    
    # Organization
    folder_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional folder to organize bookmarks"
    )
    notes = models.TextField(
        blank=True,
        max_length=500,
        help_text="Personal notes about this template"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'template_bookmarks'
        unique_together = ['user', 'template']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'folder_name']),
            models.Index(fields=['template', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} bookmarked {self.template.title}"