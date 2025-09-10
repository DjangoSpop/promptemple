# apps/chat/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()


class ChatSession(models.Model):
    """Chat session with AI models"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sessions")
    title = models.CharField(max_length=200, blank=True)
    
    # AI Model details
    ai_model = models.CharField(max_length=50, default="deepseek-chat")
    model_provider = models.CharField(max_length=50, default="deepseek")
    
    # Session metadata
    session_metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Analytics
    total_messages = models.PositiveIntegerField(default=0)
    total_tokens_used = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Template extraction
    extracted_templates_count = models.PositiveIntegerField(default=0)
    templates_approved = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "chat_sessions"
        ordering = ["-updated_at"]
        
    def __str__(self):
        return f"Chat Session {self.id} - {self.user.username}"


class ChatMessage(models.Model):
    """Individual messages in chat sessions"""
    
    MESSAGE_ROLES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    
    # Message content
    role = models.CharField(max_length=20, choices=MESSAGE_ROLES)
    content = models.TextField()
    original_content = models.TextField(blank=True)  # Store original before processing
    
    # AI response metadata
    model_used = models.CharField(max_length=50, blank=True)
    tokens_used = models.PositiveIntegerField(default=0)
    response_time_ms = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Template extraction flags
    contains_templates = models.BooleanField(default=False)
    templates_extracted = models.BooleanField(default=False)
    extraction_processed = models.BooleanField(default=False)
    
    # LangChain analysis
    langchain_analyzed = models.BooleanField(default=False)
    analysis_score = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    template_quality_score = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # Message metadata
    message_metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["role", "created_at"]),
            models.Index(fields=["contains_templates", "templates_extracted"]),
        ]
        
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class ExtractedTemplate(models.Model):
    """Templates extracted from chat conversations"""
    
    EXTRACTION_STATUS = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]
    
    TEMPLATE_QUALITY = [
        ('high', 'High Quality'),
        ('medium', 'Medium Quality'),
        ('low', 'Low Quality'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name="extracted_templates")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="extracted_templates")
    
    # Template content
    title = models.CharField(max_length=200)
    description = models.TextField()
    template_content = models.TextField()
    category_suggestion = models.CharField(max_length=100, blank=True)
    
    # Extraction metadata
    extraction_method = models.CharField(max_length=50, default="langchain")  # langchain, regex, manual
    confidence_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    quality_rating = models.CharField(max_length=20, choices=TEMPLATE_QUALITY, default='medium')
    
    # LangChain analysis
    langchain_analysis = models.JSONField(default=dict, blank=True)
    keywords_extracted = models.JSONField(default=list, blank=True)
    use_cases = models.JSONField(default=list, blank=True)
    
    # Processing status
    status = models.CharField(max_length=20, choices=EXTRACTION_STATUS, default='pending')
    auto_approved = models.BooleanField(default=False)
    
    # Template library integration
    published_template = models.OneToOneField(
        'templates.Template', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="source_extraction"
    )
    
    # Moderation
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_extractions")
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "extracted_templates"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["confidence_score", "quality_rating"]),
        ]
        
    def __str__(self):
        return f"Extracted: {self.title} ({self.status})"


class TemplateExtractionRule(models.Model):
    """Rules for automatic template extraction"""
    
    RULE_TYPES = [
        ('keyword', 'Keyword Based'),
        ('pattern', 'Pattern Matching'),
        ('langchain', 'LangChain Analysis'),
        ('ml_model', 'ML Model'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Rule configuration
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    rule_config = models.JSONField(default=dict)  # Store rule-specific configuration
    
    # Thresholds
    minimum_confidence = models.FloatField(default=0.7, validators=[MinValueValidator(0), MaxValueValidator(1)])
    auto_approve_threshold = models.FloatField(default=0.9, validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # Status
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=10)
    
    # Analytics
    total_extractions = models.PositiveIntegerField(default=0)
    successful_extractions = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "template_extraction_rules"
        ordering = ["priority", "name"]
        
    def __str__(self):
        return f"Rule: {self.name} ({self.rule_type})"
    
    @property
    def success_rate(self):
        if self.total_extractions == 0:
            return 0
        return round((self.successful_extractions / self.total_extractions) * 100, 2)


class UserTemplatePreference(models.Model):
    """User preferences for template extraction and recommendations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="template_preferences")
    
    # Extraction preferences
    auto_extract_enabled = models.BooleanField(default=True)
    auto_approve_high_confidence = models.BooleanField(default=False)
    notification_on_extraction = models.BooleanField(default=True)
    
    # Template preferences
    preferred_categories = models.JSONField(default=list, blank=True)
    excluded_categories = models.JSONField(default=list, blank=True)
    minimum_quality_threshold = models.CharField(
        max_length=20, 
        choices=ExtractedTemplate.TEMPLATE_QUALITY,
        default='medium'
    )
    
    # Monetization preferences
    contribute_to_public_library = models.BooleanField(default=True)
    allow_template_sharing = models.BooleanField(default=True)
    premium_template_access = models.BooleanField(default=False)
    
    # Analytics
    templates_contributed = models.PositiveIntegerField(default=0)
    templates_monetized = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_template_preferences"
        
    def __str__(self):
        return f"Preferences for {self.user.username}"


class TemplateMonetization(models.Model):
    """Monetization tracking for templates"""
    
    EARNING_TYPES = [
        ('usage_fee', 'Usage Fee'),
        ('premium_access', 'Premium Access'),
        ('contribution_bonus', 'Contribution Bonus'),
        ('quality_bonus', 'Quality Bonus'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey('templates.Template', on_delete=models.CASCADE, related_name="monetization_records")
    contributor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="template_earnings")
    
    # Earning details
    earning_type = models.CharField(max_length=20, choices=EARNING_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    
    # Usage context
    used_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="template_purchases")
    usage_context = models.JSONField(default=dict, blank=True)
    
    # Payment status
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "template_monetization"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["contributor", "created_at"]),
            models.Index(fields=["template", "earning_type"]),
        ]
        
    def __str__(self):
        return f"${self.amount} - {self.earning_type} for {self.template.title}"