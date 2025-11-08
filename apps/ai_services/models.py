from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
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

class AssistantThread(models.Model):
    """Conversation thread that stores the history between a user and an AI assistant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assistant_threads",
    )
    assistant_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    last_interaction_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_assistant_threads"
        ordering = ("-last_interaction_at", "-created_at")

    def touch(self):
        """Update the last interaction timestamp."""
        self.last_interaction_at = timezone.now()
        self.save(update_fields=["last_interaction_at", "updated_at"])


class AssistantMessage(models.Model):
    """Individual message within an AssistantThread."""

    ROLE_CHOICES = (
        ("system", "System"),
        ("user", "User"),
        ("assistant", "Assistant"),
        ("tool", "Tool"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(
        AssistantThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    tool_name = models.CharField(max_length=100, blank=True)
    tool_result = models.JSONField(default=dict, blank=True)
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_assistant_messages"
        ordering = ("created_at",)

    def as_openai_dict(self) -> dict:
        """Return a dict compatible with OpenAI/DeepSeek chat format."""
        message = {
            "role": self.role,
            "content": self.content,
        }
        if self.role == "tool" and self.tool_name:
            message["name"] = self.tool_name
            if self.tool_result:
                message["content"] = json.dumps(self.tool_result)
        return message


class AskMeSession(models.Model):
    """Ask-Me prompt builder session management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='askme_sessions', null=True, blank=True)

    # Session data
    intent = models.TextField(help_text="User's original intent/goal")
    spec = models.JSONField(default=dict, help_text="Current prompt specification")
    answered_vars = models.JSONField(default=dict, help_text="Variables that have been answered")

    # Current state
    current_questions = models.JSONField(default=list, help_text="Current set of questions")
    preview_prompt = models.TextField(blank=True, help_text="Preview of the generated prompt")
    final_prompt = models.TextField(blank=True, help_text="Final generated prompt")

    # Status tracking
    is_complete = models.BooleanField(default=False)
    good_enough_to_run = models.BooleanField(default=False)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'askme_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_complete', 'created_at']),
        ]

    def __str__(self):
        return f"AskMe Session: {self.intent[:50]}..."

    def initialize_spec(self):
        """Initialize the prompt specification with default structure"""
        if not self.spec:
            self.spec = {
                'goal': '',
                'audience': '',
                'tone': '',
                'style': '',
                'context': '',
                'constraints': '',
                'inputs': {},
            }
            self.save()

    def update_spec_variable(self, variable: str, value: str):
        """Update a specific variable in the spec"""
        # Ensure spec is properly initialized
        if not isinstance(self.spec, dict):
            self.initialize_spec()
        
        # Ensure answered_vars is properly initialized
        if not isinstance(self.answered_vars, dict):
            self.answered_vars = {}
        
        if variable in ['goal', 'audience', 'tone', 'style', 'context', 'constraints']:
            self.spec[variable] = value
        else:
            if 'inputs' not in self.spec:
                self.spec['inputs'] = {}
            self.spec['inputs'][variable] = value

        self.answered_vars[variable] = value
        self.updated_at = timezone.now()
        self.save()

    def get_completion_percentage(self) -> float:
        """Calculate how complete the session is based on answered variables"""
        core_fields = ['goal', 'audience', 'tone', 'style']
        answered_core = sum(1 for field in core_fields if self.spec.get(field))
        return answered_core / len(core_fields)


class AskMeQuestion(models.Model):
    """Individual questions generated for Ask-Me sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AskMeSession, on_delete=models.CASCADE, related_name='questions')

    # Question details
    qid = models.CharField(max_length=50, help_text="Unique question identifier")
    title = models.CharField(max_length=255, help_text="Question text")
    help_text = models.TextField(blank=True, help_text="Additional guidance for the user")
    variable = models.CharField(max_length=100, help_text="Variable this question maps to")

    # Question type and options
    KIND_CHOICES = [
        ('short_text', 'Short Text'),
        ('long_text', 'Long Text'),
        ('choice', 'Multiple Choice'),
        ('boolean', 'Yes/No'),
        ('number', 'Number'),
    ]
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='short_text')
    options = models.JSONField(default=list, blank=True, help_text="Options for choice questions")

    # Question properties
    is_required = models.BooleanField(default=True)
    suggested_answer = models.CharField(max_length=255, blank=True)

    # Answer tracking
    answer = models.TextField(blank=True)
    is_answered = models.BooleanField(default=False)
    answered_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    order = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'askme_questions'
        unique_together = ['session', 'qid']
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['session', 'is_answered']),
            models.Index(fields=['qid']),
        ]

    def __str__(self):
        return f"Q: {self.title}"

    def mark_answered(self, answer: str):
        """Mark the question as answered with the given answer"""
        self.answer = answer
        self.is_answered = True
        self.answered_at = timezone.now()
        self.save()

        # Update the session spec
        self.session.update_spec_variable(self.variable, answer)

    def to_dict(self) -> dict:
        """Convert question to dictionary for API responses"""
        return {
            'qid': self.qid,
            'title': self.title,
            'help_text': self.help_text,
            'kind': self.kind,
            'options': self.options,
            'variable': self.variable,
            'required': self.is_required,
            'suggested': self.suggested_answer,
            'is_answered': self.is_answered,
            'answer': self.answer,
        }
