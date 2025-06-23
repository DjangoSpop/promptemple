from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()

class AIProvider(models.Model):
    """AI service providers configuration"""
    name = models.CharField(max_length=50, unique=True)  # openai, anthropic, local
    display_name = models.CharField(max_length=100)
    api_endpoint = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    max_tokens = models.IntegerField(default=4000)
    cost_per_token = models.DecimalField(max_digits=10, decimal_places=8, default=0.0)
    rate_limit_per_hour = models.IntegerField(default=100)
    
    # Capabilities
    supports_text_analysis = models.BooleanField(default=True)
    supports_content_generation = models.BooleanField(default=True)
    supports_optimization = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_providers'

    def __str__(self):
        return self.display_name


class AIModel(models.Model):
    """Specific AI models for each provider"""
    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)  # gpt-3.5-turbo, claude-3-sonnet
    display_name = models.CharField(max_length=100)
    max_context_length = models.IntegerField(default=4000)
    cost_per_input_token = models.DecimalField(max_digits=10, decimal_places=8, default=0.0)
    cost_per_output_token = models.DecimalField(max_digits=10, decimal_places=8, default=0.0)
    
    # Performance characteristics
    response_time_avg_ms = models.IntegerField(default=2000)
    quality_score = models.FloatField(
        default=0.8, 
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_models'
        unique_together = ['provider', 'name']

    def __str__(self):
        return f"{self.provider.name}/{self.name}"


class AIInteraction(models.Model):
    """Track AI service interactions"""
    INTERACTION_TYPES = [
        ('template_analysis', 'Template Analysis'),
        ('content_optimization', 'Content Optimization'),
        ('suggestion_generation', 'Suggestion Generation'),
        ('prompt_enhancement', 'Prompt Enhancement'),
        ('keyword_extraction', 'Keyword Extraction'),
        ('sentiment_analysis', 'Sentiment Analysis'),
        ('quality_assessment', 'Quality Assessment'),
        ('personalization', 'Personalization'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_interactions')
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='interactions')
    
    # Interaction details
    interaction_type = models.CharField(max_length=50, choices=INTERACTION_TYPES)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Request/Response data
    request_prompt = models.TextField()
    request_metadata = models.JSONField(default=dict, blank=True)
    response_content = models.TextField(blank=True)
    response_metadata = models.JSONField(default=dict, blank=True)
    
    # Performance metrics
    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(null=True, blank=True)
    
    # Status and quality
    was_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    confidence_score = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    user_rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Cost tracking
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    # Related objects
    related_template = models.ForeignKey(
        'templates.Template', 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='ai_interactions'
    )
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_interactions'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['interaction_type', 'created_at']),
            models.Index(fields=['ai_model', 'was_successful']),
            models.Index(fields=['related_template', 'created_at']),
        ]

    def __str__(self):
        return f"{self.interaction_type} - {self.ai_model.name}"

    @property
    def total_tokens(self):
        return self.tokens_input + self.tokens_output

    def calculate_cost(self):
        """Calculate interaction cost based on tokens and model pricing"""
        if self.ai_model:
            input_cost = self.tokens_input * float(self.ai_model.cost_per_input_token)
            output_cost = self.tokens_output * float(self.ai_model.cost_per_output_token)
            return input_cost + output_cost
        return 0.0


class AIInsight(models.Model):
    """AI-generated insights and recommendations"""
    INSIGHT_TYPES = [
        ('optimization', 'Optimization'),
        ('suggestion', 'Suggestion'),
        ('warning', 'Warning'),
        ('recommendation', 'Recommendation'),
        ('analysis', 'Analysis'),
        ('enhancement', 'Enhancement'),
    ]
    
    INSIGHT_CATEGORIES = [
        ('template_quality', 'Template Quality'),
        ('user_experience', 'User Experience'),
        ('performance', 'Performance'),
        ('engagement', 'Engagement'),
        ('content', 'Content'),
        ('structure', 'Structure'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_insights')
    ai_interaction = models.ForeignKey(
        AIInteraction, 
        on_delete=models.CASCADE, 
        related_name='insights',
        null=True, blank=True
    )
    
    # Insight details
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPES)
    category = models.CharField(max_length=50, choices=INSIGHT_CATEGORIES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    detailed_analysis = models.TextField(blank=True)
    
    # AI metadata
    confidence = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    ai_model_used = models.CharField(max_length=100, blank=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)
    
    # Actionable recommendations
    recommendations = models.JSONField(default=list, blank=True)
    action_items = models.JSONField(default=list, blank=True)
    
    # Priority and impact
    priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='medium'
    )
    estimated_impact = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    
    # Related objects
    related_template = models.ForeignKey(
        'templates.Template', 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        related_name='ai_insights'
    )
    related_field = models.ForeignKey(
        'templates.PromptField',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='ai_insights'
    )
    
    # User interaction
    is_viewed = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    user_feedback = models.TextField(blank=True)
    user_rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ai_insights'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_viewed', 'created_at']),
            models.Index(fields=['insight_type', 'priority']),
            models.Index(fields=['related_template', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.insight_type})"


class PersonalizedRecommendation(models.Model):
    """AI-powered personalized template recommendations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    template = models.ForeignKey('templates.Template', on_delete=models.CASCADE)
    
    # Recommendation scoring
    confidence = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    relevance_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    popularity_factor = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # Reasoning and metadata
    reasoning = models.TextField()
    recommendation_factors = models.JSONField(default=list, blank=True)
    user_behavior_analysis = models.JSONField(default=dict, blank=True)
    
    # Predictions
    estimated_completion_time = models.IntegerField()  # in minutes
    predicted_success_rate = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='intermediate'
    )
    
    # Context
    recommendation_context = models.CharField(
        max_length=50,
        choices=[
            ('onboarding', 'Onboarding'),
            ('daily_use', 'Daily Use'),
            ('skill_building', 'Skill Building'),
            ('project_based', 'Project Based'),
            ('trending', 'Trending'),
        ],
        default='daily_use'
    )
    
    # User interaction
    is_viewed = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)
    interacted_at = models.DateTimeField(null=True, blank=True)
    
    # ML model info
    model_version = models.CharField(max_length=50, blank=True)
    feature_weights = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'personalized_recommendations'
        unique_together = ['user', 'template']
        ordering = ['-confidence', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_viewed', 'created_at']),
            models.Index(fields=['confidence', 'expires_at']),
        ]

    def __str__(self):
        return f"Recommendation: {self.template.title} for {self.user.username}"


class AIUsageQuota(models.Model):
    """Track AI usage quotas for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_quota')
    
    # Monthly quotas
    monthly_requests_limit = models.IntegerField(default=100)  # Free tier limit
    monthly_tokens_limit = models.IntegerField(default=50000)
    monthly_requests_used = models.IntegerField(default=0)
    monthly_tokens_used = models.IntegerField(default=0)
    
    # Daily quotas
    daily_requests_limit = models.IntegerField(default=20)
    daily_tokens_limit = models.IntegerField(default=5000)
    daily_requests_used = models.IntegerField(default=0)
    daily_tokens_used = models.IntegerField(default=0)
    
    # Reset tracking
    last_daily_reset = models.DateField(auto_now_add=True)
    last_monthly_reset = models.DateField(auto_now_add=True)
    
    # Premium features
    has_premium_ai = models.BooleanField(default=False)
    premium_expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_usage_quotas'

    def __str__(self):
        return f"AI Quota for {self.user.username}"

    def can_make_request(self, estimated_tokens=1000):
        """Check if user can make an AI request"""
        if self.has_premium_ai:
            return True
        
        if self.daily_requests_used >= self.daily_requests_limit:
            return False
        
        if self.daily_tokens_used + estimated_tokens > self.daily_tokens_limit:
            return False
        
        return True

    def consume_quota(self, tokens_used):
        """Consume AI quota for a request"""
        self.daily_requests_used += 1
        self.daily_tokens_used += tokens_used
        self.monthly_requests_used += 1
        self.monthly_tokens_used += tokens_used
        self.save()